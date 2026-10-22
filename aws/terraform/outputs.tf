output "state_machine_arn" {
  description = "Pásalo a: python -m lonxslocate barrido --aws <arn>"
  value       = aws_sfn_state_machine.barrido.arn
}

output "bucket_resultados" {
  value = aws_s3_bucket.resultados.id
}

output "lambda" {
  value = aws_lambda_function.evaluar.function_name
}

output "athena_workgroup" {
  value = aws_athena_workgroup.lonxslocate.name
}

output "github_deploy_role_arn" {
  description = "Guárdalo como secreto AWS_ROLE_ARN en GitHub"
  value       = aws_iam_role.github_deploy.arn
}
