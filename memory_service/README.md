# memory_service

Servicio HTTP en Go que provee memoria persistente al asistente Palantiri.
Corre en el servidor en el puerto `:8082` con PostgreSQL como backend.

## Endpoints

| Método | Path                              | Descripción                        |
|--------|-----------------------------------|------------------------------------|
| GET    | /health                           | Health check                       |
| POST   | /session                          | Crea una nueva sesión              |
| POST   | /message                          | Guarda un mensaje                  |
| GET    | /session/{sessionID}/messages?n=N | Últimos N mensajes de una sesión   |
| GET    | /search?q=keyword&limit=N         | Búsqueda por keyword en mensajes   |

---

## Setup inicial del servidor (una sola vez)

### 1. Clonar el repo en el servidor

```bash
ssh user@<SERVER_IP>
git clone <url-del-repo> ~/Palantiri
```

### 2. Correr el script de setup

Desde el servidor, en el directorio del servicio:

```bash
cd ~/Palantiri/memory_service
chmod +x setup_server.sh
sudo ./setup_server.sh
```

Esto instala PostgreSQL, crea el usuario `palantiri_user`, la base de datos `palantiri_db`,
aplica el schema y guarda las credenciales en `/etc/memory_service.env`.

Al finalizar, el script imprime la password generada — **anotarla**, se necesita para el cliente Python.

---

## Deploy

Ajustar `REPO_PATH` en `deploy.sh` con el path real del repo en el servidor, luego correr
desde tu máquina local:

```bash
chmod +x deploy.sh
./deploy.sh
```

El script se conecta por SSH al servidor, compila el binario en Go, lo instala en
`/usr/local/bin/memory_service` y registra/reinicia el servicio systemd.

Para deploys posteriores (cuando hay cambios en el código), hacer `git pull` en el servidor
y volver a correr `./deploy.sh`.

---

## Manejo del servicio

```bash
sudo systemctl status memory_service    # ver estado
sudo systemctl restart memory_service   # reiniciar
sudo journalctl -u memory_service -f    # ver logs en tiempo real
```

---

## Variables de entorno

El servicio lee sus credenciales desde `/etc/memory_service.env`:

```
PGHOST=localhost
PGPORT=5432
PGUSER=palantiri_user
PGPASSWORD=<generado por setup_server.sh>
PGDATABASE=palantiri_db
```
