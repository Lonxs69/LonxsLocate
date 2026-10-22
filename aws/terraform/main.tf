data "aws_caller_identity" "actual" {}

locals {
  nombre  = "lonxslocate-${var.entorno}"
  raiz    = "${path.module}/../.."
  bucket  = "${local.nombre}-${data.aws_caller_identity.actual.account_id}"
  db_glue = replace(local.nombre, "-", "_")
  paquete = fileset("${local.raiz}/lonxslocate", "*.py")
}

# ---------------------------------------------------------------------------
# S3: data lake de resultados + salida de Athena
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "resultados" {
  bucket = local.bucket
}

resource "aws_s3_bucket_public_access_block" "resultados" {
  bucket                  = aws_s3_bucket.resultados.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "resultados" {
  bucket = aws_s3_bucket.resultados.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "resultados" {
  bucket = aws_s3_bucket.resultados.id

  rule {
    id     = "limpiar-salidas-athena"
    status = "Enabled"
    filter {
      prefix = "athena/"
    }
    expiration {
      days = 30
    }
  }

  rule {
    id     = "resultados-a-ia"
    status = "Enabled"
    filter {
      prefix = "resultados/"
    }
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }
}

# ---------------------------------------------------------------------------
# Lambda: evalúa una configuración de constelación
# ---------------------------------------------------------------------------
data "archive_file" "lambda" {
  type        = "zip"
  output_path = "${path.module}/.build/lambda.zip"

  source {
    content  = file("${local.raiz}/aws/lambda/handler.py")
    filename = "handler.py"
  }

  source {
    content  = file("${local.raiz}/data/estaciones.csv")
    filename = "data/estaciones.csv"
  }

  dynamic "source" {
    for_each = local.paquete
    content {
      content  = file("${local.raiz}/lonxslocate/${source.value}")
      filename = "lonxslocate/${source.value}"
    }
  }
}

resource "aws_iam_role" "lambda" {
  name = "${local.nombre}-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.resultados.arn}/resultados/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.lambda.arn}:*"
      },
    ]
  })
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.nombre}-evaluar"
  retention_in_days = 14
}

resource "aws_lambda_function" "evaluar" {
  function_name    = "${local.nombre}-evaluar"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  architectures    = ["arm64"]
  handler          = "handler.handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  memory_size      = var.lambda_memoria_mb
  timeout          = 120

  environment {
    variables = {
      RESULTADOS_BUCKET = aws_s3_bucket.resultados.id
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ---------------------------------------------------------------------------
# Glue + Athena: tabla consultable sobre los resultados
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "lonxslocate" {
  name = local.db_glue
}

resource "aws_glue_catalog_table" "resultados" {
  name          = "resultados"
  database_name = aws_glue_catalog_database.lonxslocate.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "json"
    "projection.enabled"        = "true"
    "projection.barrido.type"   = "injected"
    "storage.location.template" = "s3://${aws_s3_bucket.resultados.id}/resultados/barrido=$${barrido}/"
  }

  partition_keys {
    name = "barrido"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.resultados.id}/resultados/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "planos"
      type = "int"
    }
    columns {
      name = "sats_por_plano"
      type = "int"
    }
    columns {
      name = "altitud_km"
      type = "double"
    }
    columns {
      name = "inclinacion_deg"
      type = "double"
    }
    columns {
      name = "total_satelites"
      type = "int"
    }
    columns {
      name = "cobertura_min_pct"
      type = "double"
    }
    columns {
      name = "cobertura_media_pct"
      type = "double"
    }
    columns {
      name = "hueco_maximo_min"
      type = "double"
    }
    columns {
      name = "peor_estacion"
      type = "string"
    }
    columns {
      name = "visibles_promedio"
      type = "double"
    }
  }
}

resource "aws_athena_workgroup" "lonxslocate" {
  name          = local.nombre
  force_destroy = true

  configuration {
    enforce_workgroup_configuration = true
    bytes_scanned_cutoff_per_query  = 1073741824 # 1 GB: tope de costo por consulta

    result_configuration {
      output_location = "s3://${aws_s3_bucket.resultados.id}/athena/"
    }
  }
}

# ---------------------------------------------------------------------------
# Step Functions: reparte el barrido y al final rankea con Athena
# ---------------------------------------------------------------------------
resource "aws_iam_role" "sfn" {
  name = "${local.nombre}-sfn"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "sfn" {
  role = aws_iam_role.sfn.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = [aws_lambda_function.evaluar.arn, "${aws_lambda_function.evaluar.arn}:*"]
      },
      {
        Effect   = "Allow"
        Action   = ["athena:StartQueryExecution", "athena:GetQueryExecution", "athena:GetQueryResults", "athena:StopQueryExecution"]
        Resource = aws_athena_workgroup.lonxslocate.arn
      },
      {
        Effect = "Allow"
        Action = ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"]
        Resource = [
          "arn:aws:glue:${var.region}:${data.aws_caller_identity.actual.account_id}:catalog",
          aws_glue_catalog_database.lonxslocate.arn,
          aws_glue_catalog_table.resultados.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:GetBucketLocation"]
        Resource = [aws_s3_bucket.resultados.arn, "${aws_s3_bucket.resultados.arn}/*"]
      },
    ]
  })
}

resource "aws_sfn_state_machine" "barrido" {
  name     = "${local.nombre}-barrido"
  role_arn = aws_iam_role.sfn.arn
  definition = templatefile("${path.module}/barrido.asl.json", {
    lambda_arn         = aws_lambda_function.evaluar.arn
    workgroup          = aws_athena_workgroup.lonxslocate.name
    base_datos         = aws_glue_catalog_database.lonxslocate.name
    concurrencia       = var.concurrencia_maxima
    cobertura_objetivo = var.cobertura_objetivo
  })
}
