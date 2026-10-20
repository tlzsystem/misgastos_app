# MisGastos — Gestión de Gastos e Ingresos Mensuales (Django)

Aplicación web monolítica multi-usuario desarrollada en **Django** para el control de finanzas personales mensuales. Permite a cada usuario administrar sus propias categorías de ingresos y gastos (crear, editar, activar/desactivar) y registrar, editar o eliminar movimientos asociados a dichas categorías con paneles analíticos e indicadores interactivos.

---

## Características Principales

- **Arquitectura Multi-usuario con Aislamiento Estricto**: Cada usuario registrado posee su propio catálogo de categorías y movimientos completamente aislado a nivel de vistas, formularios y validaciones de modelo.
- **Gestión de Categorías (Ingresos y Gastos)**:
  - Creación y edición con selector de color, ícono identificatorio y presupuesto mensual opcional.
  - Activación / Desactivación (`is_active`) sin pérdida del historial de movimientos previos.
  - Carga opcional en un clic de categorías sugeridas al registrarse o desde el panel de categorías.
- **Gestión de Movimientos**:
  - Registro, edición y eliminación de movimientos asociados obligatoriamente a una categoría activa del usuario.
  - Filtros combinados por mes, año, tipo (Ingreso/Gasto), categoría y búsqueda por texto.
- **Dashboard Mensual Moderno**:
  - KPIs de Ingresos del Mes, Gastos del Mes, Balance Neto, Variación porcentual contra el mes anterior y Tasa de Ahorro.
  - Gráficos interactivos con **Chart.js** (Flujo Diario de Ingresos vs Gastos y Distribución de Gastos por Categoría).
  - Barras de progreso de presupuesto por categoría.
- **Buenas Prácticas de Configuración en Django**:
  - Entorno virtual local (`venv`).
  - Variables de entorno mediante `.env` (`django-environ`).
  - Separación modular de configuraciones por ambiente:
    - `config/settings/base.py`: Configuración común.
    - `config/settings/dev.py`: Configuración para desarrollo local (`DEBUG=True`, SQLite local, consola de correo).
    - `config/settings/prod.py`: Configuración para producción (`DEBUG=False`, cabeceras de seguridad HTTPS/HSTS, cookies seguras, WhiteNoise comprimido y soporte para PostgreSQL).

---

## Estructura del Proyecto

```text
MisGastos/
├── apps/
│   ├── accounts/               # Autenticación, registro y perfil de usuario
│   └── finances/               # Modelos Category y Movement, vistas, servicios y tests
├── config/
│   ├── settings/
│   │   ├── base.py             # Configuración base compartida
│   │   ├── dev.py              # Configuración de desarrollo
│   │   └── prod.py             # Configuración de producción
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── static/
│   └── css/styles.css
├── templates/
│   ├── base.html
│   ├── accounts/
│   └── finances/
├── .env                        # Variables de entorno locales (no versionado)
├── .env.example                # Plantilla de variables de entorno
├── manage.py
└── requirements.txt
```

---

## Ejecución en Desarrollo Local

1. **Activar el entorno virtual**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Instalar dependencias** (ya instaladas en `venv`):
   ```powershell
   pip install -r requirements.txt
   ```

3. **Ejecutar migraciones**:
   ```powershell
   python manage.py migrate
   ```

4. **(Opcional) Cargar usuario y datos de demostración**:
   ```powershell
   python manage.py seed_demo
   ```
   - **Usuario demo**: `demo`
   - **Contraseña**: `demo12345`

5. **Iniciar el servidor de desarrollo**:
   ```powershell
   python manage.py runserver
   ```
   Luego abre en tu navegador: `http://127.0.0.1:8000/`

---

## Uso en Producción

Para ejecutar en producción, define en tu `.env` o variables del sistema:
```env
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False
SECRET_KEY=clave-secreta-segura-de-produccion
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DATABASE_URL=postgres://usuario:password@host:5432/nombre_db
```
Y recolecta los archivos estáticos:
```bash
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```
