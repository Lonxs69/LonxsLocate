# LonxsLocate en AWS

Barrido masivo de constelaciones: cada configuración se evalúa en su propia Lambda, en paralelo, y Athena rankea los resultados.

## Despliegue

Requisitos: Terraform ≥ 1.6, credenciales de administrador para el primer `apply` y un bucket S3 para el estado.

```bash
cd aws/terraform
terraform init -backend-config="bucket=<tu-bucket-de-estado>"
terraform apply -var="entorno=dev"
```

> Si la cuenta ya tiene el proveedor OIDC de GitHub, agrega `-var="crear_proveedor_oidc=false"`.

Con las salidas de Terraform, configura el repositorio en GitHub (Settings → Secrets and variables → Actions):

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `AWS_ROLE_ARN` | salida `github_deploy_role_arn` |
| Variable | `LAMBDA_NAME` | salida `lambda` |
| Variable | `STATE_MACHINE_ARN` | salida `state_machine_arn` |
| Variable | `AWS_REGION` | región usada (opcional) |

Ningún ARN, ID de cuenta ni llave queda escrito en el código.

## Uso

```bash
pip install ".[aws]"
python -m lonxslocate barrido --aws "$(terraform -chdir=aws/terraform output -raw state_machine_arn)"
```

O desde GitHub: **Actions → Desplegar en AWS → Run workflow** con *lanzar barrido* activado.

Consultas de ejemplo para Athena en [`athena/consultas.sql`](athena/consultas.sql).

## Seguridad

- Bucket privado (Block Public Access), cifrado SSE-S3 y ciclo de vida para limpiar salidas de Athena.
- La Lambda solo puede escribir en `resultados/` y en su propio log.
- El rol de GitHub solo puede actualizar el código de esa Lambda y lanzar ese Step Functions, y solo desde la rama `main` de este repo.
- Athena corta cualquier consulta que escanee más de 1 GB.

## Eliminar todo

```bash
terraform destroy
```
