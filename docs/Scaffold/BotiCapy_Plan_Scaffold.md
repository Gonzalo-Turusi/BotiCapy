# BotiCapy — Plan de Scaffold del Proyecto

> Bot de Discord modular, gratuito, con IA. Este documento es el plan de referencia para que Windsurf genere la estructura inicial del proyecto.

---

## 1. Stack tecnológico (vigente a agosto 2026)

| Componente | Elección | Versión de referencia |
|---|---|---|
| Lenguaje | Python | **3.12+** (recomendado 3.13; evitar 3.14 todavía por soporte de librerías) |
| Librería Discord | `discord.py` | **2.6.4** (última estable, activamente mantenida) |
| IA principal | Groq SDK | **1.6.0** — gratis, rápido, sin tarjeta |
| IA fallback | `google-genai` (SDK oficial nuevo de Google, reemplaza al viejo `google-generativeai`) | última en PyPI |
| Config / validación | `pydantic` + `pydantic-settings` | última estable |
| HTTP async | `httpx` | última estable (dependencia de los SDKs de IA igual) |
| Variables de entorno | `python-dotenv` | última estable |
| Logging | `logging` (stdlib) | — |

**Por qué `google-genai` y no `google-generativeai`:** Google discontinuó el SDK viejo; el reemplazo oficial es el paquete `google-genai` (`from google import genai`). Si Windsurf o alguna guía vieja sugiere `google-generativeai`, hay que ignorarlo — está obsoleto.

**Slash commands, no prefix commands:** Vamos a usar exclusivamente `app_commands` (el sistema de slash commands de discord.py). No usamos `commands.command()` con prefijo (`!comando`) porque desde 2026 depende del Message Content Intent y ya no es el estándar recomendado por Discord.

---

## 2. Principios de diseño

- **Separación de responsabilidades por carpeta**, no por capas técnicas abstractas. Cada carpeta tiene un propósito claro y nada se mezcla.
- **Interfaces livianas con `typing.Protocol`** (el equivalente Python a una interfaz de C#) solo donde de verdad aporta: por ejemplo, para que `AIService` no dependa directamente de Groq o Gemini, sino de un contrato `AIProvider`. Esto permite cambiar de proveedor o agregar uno nuevo sin tocar el resto del código.
- **Sin sobre-ingeniería**: no vamos a crear abstracciones para cosas que hoy tienen una sola implementación y no lo necesitan (ej: no hace falta una interfaz para el cliente de Discord en sí).
- **Inyección de dependencias simple y manual**: los servicios (como `AIService`) se instancian una vez en el arranque del bot y se pasan a los Cogs — no usamos un framework de DI, solo pasar objetos por constructor.
- **Cada Feature es autocontenida**: su propio Cog, su propio servicio si lo necesita, sin lógica de negocio filtrada a otras carpetas.

---

## 3. Estructura de carpetas

```
BotiCapy/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── bot.py                          # Entry point — arranca el bot
│
├── core/                           # Lo mínimo indispensable para que el bot exista y funcione
│   ├── __init__.py
│   ├── bot_client.py                # Clase BotiCapyClient(commands.Bot): setup_hook, carga de Cogs
│   ├── config.py                     # Settings (pydantic-settings) — lee .env, tipado fuerte
│   ├── logger.py                      # Configuración central de logging
│   └── errors.py                       # Excepciones propias + handler global de errores de comandos
│
├── features/                       # Slash commands, organizados por carpeta (1 feature = 1 carpeta)
│   ├── __init__.py
│   └── joke/
│       ├── __init__.py
│       ├── commands.py               # Cog con el slash command /chiste
│       └── service.py                 # JokeService: arma el prompt, llama a AIService
│   # A futuro: features/art_judge/, features/xp/ (con subcomandos activar/desactivar), etc.
│
├── modules/                        # Features grandes: listeners de canal, background tasks, multi-comando
│   └── __init__.py
│   # A futuro: modules/aniguess/, modules/chat_channel/, modules/ranking/
│
├── models/                         # Modelos de datos tipados (pydantic / dataclasses)
│   ├── __init__.py
│   └── ai.py                         # AIRequest, AIResponse, etc.
│
└── shared/                         # Todo lo transversal: IA, base de datos, cooldowns, historial de comandos
    ├── __init__.py
    ├── ai/
    │   ├── __init__.py
    │   ├── base.py                     # Protocol AIProvider (la "interfaz")
    │   ├── groq_provider.py             # Implementación con Groq
    │   ├── gemini_provider.py            # Implementación con Gemini (fallback)
    │   └── ai_service.py                  # Orquesta: intenta primario, si falla usa fallback
    ├── cooldowns.py                    # Manejo simple de cooldowns por usuario/comando (en memoria por ahora)
    └── database/
        └── __init__.py                  # Placeholder — a futuro SQLite para historial, XP, etc.
```

**Regla simple para decidir dónde va algo nuevo:**
- ¿Es indispensable para que el bot prenda y ande? → `core/`
- ¿Es un slash command (o un par de comandos relacionados, como activar/desactivar algo)? → `features/<nombre>/`
- ¿Necesita escuchar mensajes, correr en background, o es más grande que un comando? → `modules/<nombre>/`
- ¿Es una forma de tipar datos que se pasan entre capas? → `models/`
- ¿Lo van a usar dos o más features/modules distintos (IA, DB, cooldowns)? → `shared/`

---

## 4. Diseño de la capa de IA (`shared/ai/`)

Esta es la parte donde vale la pena la abstracción, porque vamos a tener 2 proveedores (Groq primario, Gemini fallback) y en el futuro tal vez más.

**`shared/ai/base.py`**
```python
from typing import Protocol

class AIProvider(Protocol):
    """Contrato que debe cumplir cualquier proveedor de IA."""
    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        ...
```

**`shared/ai/groq_provider.py`** y **`shared/ai/gemini_provider.py`**
Cada uno implementa `generate()` usando su SDK respectivo (`groq` / `google-genai`). No exponen nada más que eso hacia afuera — si mañana cambia la librería interna de alguno, el resto del bot ni se entera.

**`shared/ai/ai_service.py`**
```python
class AIService:
    def __init__(self, primary: AIProvider, fallback: AIProvider):
        self._primary = primary
        self._fallback = fallback

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        try:
            return await self._primary.generate(prompt, system_prompt)
        except Exception:
            # log del error acá
            return await self._fallback.generate(prompt, system_prompt)
```

`AIService` es lo único que las features conocen — nunca importan `groq` o `google-genai` directamente. Esto es lo que te va a permitir, por ejemplo, meter un tercer proveedor gratis el día de mañana sin tocar ninguna feature.

---

## 5. Primer comando: `/chiste` (feature `joke`)

**Comportamiento:** el usuario ejecuta `/chiste palabra:<algo>` y la IA devuelve un chiste corto usando esa palabra.

**`features/joke/commands.py`**
```python
from discord import app_commands, Interaction
from discord.ext import commands
from features.joke.service import JokeService

class JokeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, joke_service: JokeService):
        self.bot = bot
        self.joke_service = joke_service

    @app_commands.command(name="chiste", description="La IA hace un chiste con la palabra que le des")
    @app_commands.describe(palabra="Palabra que el chiste debe incluir")
    async def chiste(self, interaction: Interaction, palabra: str):
        await interaction.response.defer()  # la IA puede tardar más de 3s
        chiste = await self.joke_service.generar_chiste(palabra)
        await interaction.followup.send(chiste)

async def setup(bot: commands.Bot):
    await bot.add_cog(JokeCog(bot, bot.ai_service))  # ai_service inyectado desde bot_client.py
```

**`features/joke/service.py`**
```python
from shared.ai.ai_service import AIService

SYSTEM_PROMPT = (
    "Sos un comediante argentino, breve y ocurrente. "
    "Contás un solo chiste corto (máximo 3 líneas), sin explicaciones extra."
)

class JokeService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def generar_chiste(self, palabra: str) -> str:
        prompt = f"Hacé un chiste corto que use la palabra '{palabra}'."
        return await self.ai_service.generate(prompt, system_prompt=SYSTEM_PROMPT)
```

Este mismo patrón (`commands.py` + `service.py`) es el molde que se repite para cada feature nueva.

---

## 6. Pasos para que Windsurf scaffoldee el proyecto

1. Crear la carpeta raíz `BotiCapy/` con la estructura completa de la sección 3 (todas las carpetas y `__init__.py` vacíos donde corresponda).
2. Generar `requirements.txt` (ver sección 8).
3. Generar `.env.example` (ver sección 9).
4. Generar `.gitignore` estándar de Python + `.env` + `__pycache__/` + `.venv/`.
5. Implementar `core/config.py` con `pydantic-settings`, leyendo: `DISCORD_TOKEN`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `LOG_LEVEL`.
6. Implementar `core/logger.py`: configuración básica de logging a consola (formato con timestamp y nivel).
7. Implementar `shared/ai/base.py`, `groq_provider.py`, `gemini_provider.py`, `ai_service.py` según sección 4.
8. Implementar `core/bot_client.py`: clase que extiende `commands.Bot`, instancia `AIService` una sola vez en `setup_hook`, lo guarda como atributo (`self.ai_service`), y carga automáticamente todas las extensions (Cogs) dentro de `features/` y `modules/` (usar `bot.load_extension()` iterando carpetas, no hardcodear cada import).
9. Implementar `core/errors.py`: handler global para `app_commands` (capturar errores de cooldown, permisos, o fallos de la IA y responder algo amigable en vez de que el comando falle en silencio).
10. Implementar la feature `joke` completa (sección 5).
11. Implementar `bot.py`: carga `.env`, instancia `BotiCapyClient`, sincroniza los slash commands (`tree.sync()`), corre el bot con el token.
12. Probar localmente con el bot invitado a un server de test antes de tocar deploy.

---

## 7. Variables de entorno necesarias

**`.env.example`**
```
DISCORD_TOKEN=
GROQ_API_KEY=
GEMINI_API_KEY=
LOG_LEVEL=INFO
```

---

## 8. `requirements.txt` sugerido

```
discord.py==2.6.4
groq>=1.6.0
google-genai>=1.22.0
pydantic>=2.9
pydantic-settings>=2.6
python-dotenv>=1.0
httpx>=0.27
```

*(Windsurf debería fijar las versiones exactas disponibles al momento de instalar, estas son mínimas de referencia.)*

---

## 9. Cuentas y credenciales gratuitas a crear

| Servicio | Para qué | Link |
|---|---|---|
| Discord Developer Portal | Token del bot, intents, invitación | discord.com/developers/applications |
| Groq Console | API key IA principal (gratis, sin tarjeta) | console.groq.com |
| Google AI Studio | API key Gemini, fallback (gratis, sin tarjeta) | aistudio.google.com |
| Oracle Cloud | VM gratis 24/7 para el deploy | cloud.oracle.com/free |
| GitHub | Repo del proyecto | github.com |

**Configuración del bot en Discord Developer Portal:**
1. New Application → nombre `BotiCapy`.
2. Sección "Bot" → Reset Token → guardar en `.env` local (nunca subir a GitHub).
3. En "Privileged Gateway Intents": por ahora **no hace falta activar Message Content** (el `/chiste` no lee mensajes, solo recibe el parámetro del slash command). Se activa más adelante cuando implementemos módulos que sí lean el chat (ranking, canal de IA libre).
4. En "OAuth2 → URL Generator": marcar scopes `bot` y `applications.commands`, permisos mínimos (Send Messages, Use Slash Commands, Embed Links). Copiar el link generado e invitarlo al server.

---

## 10. Deploy gratuito (Oracle Cloud)

1. Crear cuenta en Oracle Cloud → activar el **Always Free Tier**.
2. Levantar una instancia **Ampere A1 (ARM)** — gratis permanente, alcanza y sobra para este bot (hasta 4 OCPU / 24GB RAM disponibles en el tier free, un bot de Discord chico usa una fracción mínima de eso).
3. Elegir imagen **Ubuntu** (22.04 o 24.04 LTS).
4. Configurar acceso SSH con la key que genera Oracle al crear la instancia.
5. Conectarse por SSH e instalar: `python3.12`, `pip`, `git`.
6. `git clone` del repo de BotiCapy.
7. Crear entorno virtual: `python3.12 -m venv .venv && source .venv/bin/activate`.
8. `pip install -r requirements.txt`.
9. Crear el `.env` real en el servidor (con los valores reales, nunca el que está en git).
10. Correr el bot como servicio con **systemd** (no dejarlo corriendo en una sesión de SSH que se puede cortar):
    - Crear `/etc/systemd/system/boticapy.service` apuntando al `.venv` y a `bot.py`.
    - `systemctl enable boticapy` (arranca solo si la VM reinicia) y `systemctl start boticapy`.
11. Ver logs con `journalctl -u boticapy -f` para debuggear en vivo.

No hace falta Docker para este approach — es más simple de entender y debuggear a esta escala, y se puede sumar Docker más adelante si el proyecto crece.

---

## 11. Qué queda fuera de este primer scaffold (a propósito)

- Base de datos (SQLite) — se agrega en `shared/database/` cuando implementemos la primera feature que necesite persistencia (ej: cooldowns persistentes, historial de comandos, XP).
- `modules/` queda vacío por ahora — se llena cuando encaremos algo que lea canales (ranking, chat con IA, AniGuess).
- CI/CD (GitHub Actions) — se suma cuando el ciclo de "hacer cambio → subir al VM a mano" empiece a resultar tedioso, no antes.

Mantener el scaffold inicial lo más chico posible que siga siendo correcto es intencional: cada carpeta nueva se crea cuando hay una razón concreta, no antes.
