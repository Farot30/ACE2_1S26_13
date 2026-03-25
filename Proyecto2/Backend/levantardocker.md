Aquí tienes todo el flujo completo:

---

**1. Iniciar sesión en Docker Hub**
```bash
docker login
# te pedirá:
# Username: farot3
# Password: tu contraseña
```

---

**2. Construir y subir las imágenes**

Para el backend (desde la carpeta del backend):
```bash
docker build -t farot3/park-guard-backend:latest -t farot3/park-guard-backend:v1.0 .
docker push farot3/park-guard-backend --all-tags
```

Para el consumer (misma carpeta del backend):
```bash
docker build -f Dockerfile.consumer -t farot3/park-guard-consumer:latest -t farot3/park-guard-consumer:v1.0 .
docker push farot3/park-guard-consumer --all-tags
```

Para el frontend (desde la carpeta del frontend):
```bash
docker build -t farot3/park-guard-frontend:latest -t farot3/park-guard-frontend:v1.0 .
docker push farot3/park-guard-frontend --all-tags
```

---

**3. Levantar el sistema el día de la presentación**

Esto es lo importante — el día de la presentación el sistema debe descargarse desde Docker Hub, no construirse localmente. Desde la carpeta donde está el `docker-compose.yml`:

```bash
# Descarga todas las imágenes desde Docker Hub
docker compose pull

# Levanta todos los contenedores
docker compose up
```

O en un solo comando:
```bash
docker compose up --pull always
```

---

**4. Comandos útiles durante la presentación**

Ver que todos los contenedores estén corriendo:
```bash
docker compose ps
```

Ver logs de un servicio específico:
```bash
docker compose logs backend
docker compose logs consumer
docker compose logs frontend
```

Ver logs en tiempo real:
```bash
docker compose logs -f
```

Bajar todo:
```bash
docker compose down
```

Bajar todo y eliminar volúmenes (resetear base de datos):
```bash
docker compose down -v
```

---

**5. Flujo completo antes de la presentación**

```
1. docker login
2. Construir y pushear las 3 imágenes (pasos 2)
3. Verificar en hub.docker.com que aparecen las 3 imágenes
4. El día de la presentación: docker compose pull && docker compose up
```

Lo más importante es que el día de la presentación el evaluador verá que las imágenes se descargan de Docker Hub con `docker compose pull`, demostrando que están publicadas correctamente.