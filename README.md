# RastroWatch

RastroWatch es una aplicación web privada para registrar, consultar y valorar relojes de segunda mano vistos en rastrillos, Wallapop, tiendas o particulares.

> **RastroWatch:** “Escanea, registra y aprende el valor real de relojes de segunda mano.”

## Stack

- Backend: FastAPI
- Frontend: React + Vite servido con Nginx
- Base de datos: PostgreSQL
- Despliegue: Docker Compose
- Imágenes: carpeta local `./uploads` montada en `/app/uploads`
- Acceso: login simple con usuario administrador definido por variables de entorno

## Estructura recomendada en Ubuntu

```text
/opt/rastrowatch
├── backend
├── frontend
├── uploads
├── docker-compose.yml
├── .env.example
└── README.md
```

## Puesta en marcha

```bash
cd /opt/rastrowatch
cp .env.example .env
nano .env
```

Cambia al menos `POSTGRES_PASSWORD`, `ADMIN_PASSWORD` y `SESSION_SECRET`.

Levantar la app:

```bash
docker compose up -d --build
```

Acceder desde el navegador:

```text
http://IP_DEL_SERVIDOR:8085
```

## Comandos útiles

Parar la app:

```bash
docker compose down
```

Ver logs de todos los servicios:

```bash
docker compose logs -f
```

Ver logs del backend:

```bash
docker compose logs -f backend
```

Reiniciar tras cambios:

```bash
docker compose up -d --build
```

## Backups

Crear backup de PostgreSQL:

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backups/rastrowatch-$(date +%F).sql
```

Crear copia de imágenes:

```bash
tar -czf backups/uploads-$(date +%F).tar.gz uploads
```

Restaurar base de datos desde un backup:

```bash
cat backups/rastrowatch-AAAA-MM-DD.sql | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

Restaurar imágenes:

```bash
tar -xzf backups/uploads-AAAA-MM-DD.tar.gz
```

## Funcionalidades incluidas

- Login privado con credenciales de entorno.
- Dashboard responsive con buscador por marca, modelo, referencia y notas.
- Tarjetas con imagen principal, precio recomendado o visto, oportunidad y riesgo.
- CRUD completo de relojes con campos técnicos, valoración, fuentes y notas de aprendizaje.
- Formulario rápido “Reloj visto” con foto, marca/modelo opcionales, precio, ubicación y notas.
- Página de detalle con fotos, datos técnicos, valoración, máximo recomendado, alertas e identificación.
- Valoración básica sin IA real:
  - Precio bajo mínimo estimado: oportunidad muy buena.
  - Precio entre mínimo y medio: buena.
  - Precio entre medio y máximo: normal.
  - Precio por encima del máximo: mala / evitar.
  - Estado “sin probar”: reduce la valoración.
  - Riesgo de falsificación alto: muestra advertencia fuerte.
- Endpoint preparado para IA futura: `POST /api/ai/analyze`, actualmente responde `IA pendiente de configurar`.

## Notas de despliegue

- El frontend se expone en el puerto externo `8085`.
- El backend queda accesible internamente para Nginx y Docker Compose.
- Los ficheros subidos persisten en `./uploads`.
- PostgreSQL persiste en el volumen Docker `postgres_data`.
- No se usan servicios externos, APIs de pago ni IA real.

## Tasador IA automático

La pantalla **Tasador IA** permite subir una foto, indicar precio visto, ubicación y notas. El backend guarda la imagen, intenta identificar el reloj con OpenAI Vision si hay clave configurada, busca precios en las fuentes disponibles, calcula una valoración y guarda una investigación completa en PostgreSQL.

El sistema calcula de forma aproximada:

- valor de mercado inicial;
- valor real aproximado actual en rango bajo/medio/alto;
- precio recomendado de compra;
- valor probable de venta;
- margen posible de reventa;
- oportunidad y recomendación: comprar, negociar, investigar más o evitar.

Si faltan claves de API, la aplicación sigue funcionando. Las fuentes no disponibles aparecen como **No configurada** y el análisis puede guardarse como pendiente con “datos insuficientes”.

### Configurar OpenAI

En `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=
```

Si `OPENAI_MODEL` queda vacío, el backend usa el modelo de visión configurado por defecto. La IA devuelve JSON estricto con marca, modelo, referencia, estado visual, daños, riesgo de autenticidad, confianza y queries de búsqueda. Si `OPENAI_API_KEY` está vacío, la identificación por IA se desactiva y se muestra un aviso.

### Configurar eBay

Crea credenciales de aplicación en eBay Developers y rellena:

```bash
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_MARKETPLACE=EBAY_ES
```

RastroWatch usa OAuth client credentials y la Browse API para normalizar resultados de precio.

### Configurar TheWatchAPI

```bash
THEWATCHAPI_KEY=...
```

Se usa para validar datos técnicos y precios orientativos cuando la API está disponible.

### Configurar WatchCharts

```bash
WATCHCHARTS_API_KEY=...
```

Se usa para consultar precios de mercado si la cuenta/API contratada lo permite.

### Configurar Apify

```bash
APIFY_TOKEN=...
APIFY_WALLAPOP_ACTOR_ID=...
APIFY_MILANUNCIOS_ACTOR_ID=...
APIFY_CATAWIKI_ACTOR_ID=...
```

Cada actor se ejecuta solo si existe token y actor configurado. Si un actor falla o agota el tiempo, la búsqueda continúa con el resto de fuentes y se guarda el error en `raw` para depuración.

## Actualizar despliegue en Ubuntu

```bash
cd /opt/rastrowatch
git pull
cp .env.example .env # solo si no existe todavía; no sobrescribas tus claves
docker compose up -d --build
```

Ver logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

## Limitaciones del tasador

- La valoración es aproximada y depende de las fuentes externas configuradas.
- El estado real debe revisarse manualmente con el reloj en mano.
- RastroWatch no garantiza autenticidad ni detecta todas las falsificaciones.
- No se inventan precios: si no hay resultados suficientes se muestra “datos insuficientes”.
- Las APIs externas pueden cambiar formato, límites o permisos; los errores se controlan para no bloquear toda la búsqueda.
