# Toolchain y reproducción exacta

Ejecutado: Lean 4.19.0, Linux x86_64, commit `6caaee842e94`, release oficial.
No se modificó configuración global ni se instaló en el PC del usuario.

- Archivo descargado: `https://github.com/leanprover/lean4/releases/download/v4.19.0/lean-4.19.0-linux.tar.zst`
- SHA256 del archivo descargado: `6fe3ce97a58f44e2b3567d455b994eacec5bfe9ae7774f2a573444480ba813fe`
- SHA256 del ejecutable usado: `92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023`

Los hashes registran los bytes observados; no son una firma independiente del proveedor.

```sh
mkdir -p /tmp/cryptosure-lean
curl -L --fail --silent --show-error \
  https://github.com/leanprover/lean4/releases/download/v4.19.0/lean-4.19.0-linux.tar.zst \
  -o /tmp/cryptosure-lean/lean.tar.zst
sha256sum /tmp/cryptosure-lean/lean.tar.zst
tar --zstd -xf /tmp/cryptosure-lean/lean.tar.zst -C /tmp/cryptosure-lean
python3 run_checks.py --lean /tmp/cryptosure-lean/lean-4.19.0-linux/bin/lean
```

Comparar el hash antes de extraer y ejecutar. En este entorno la lectura de red necesitó la capacidad de red del comando; no se usaron credenciales.

`lake build` también se ejecutó correctamente. Se pueden eliminar y regenerar `.lake/`, `*.olean` y `lake-manifest.json`; no se necesita conservar el archivo de 328 MiB de Lean dentro del paquete de investigación.

La evidencia principal es `results/verification.json`; cada intento también conserva `verification-<run_id>.json`. El último recibo se reemplaza atómicamente: in_progress al comenzar, failed ante error y verified sólo tras los checks solicitados. Una versión nueva de Lean debe calificarse como una nueva ejecución, no usar el resultado viejo con el número cambiado.
