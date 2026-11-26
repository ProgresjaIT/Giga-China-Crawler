Zignoruj poniżej

Najprościej zrobiłbym to w oparciu o Docker + konfigurację środowiska per repozytorium, zamiast próbować instalować wszystkie zależności i narzędzia bezpośrednio w OpenHands.

Kluczowa zasada: OpenHands powinien być uniwersalnym orchestratoriem agentów, a każde repozytorium powinno mieć własne, niezależne środowisko wykonawcze.

Dzięki temu:

Jedno repozytorium może korzystać z Claude Code.
Drugie może korzystać z Codex CLI.
Trzecie może mieć Pythona, CUDA, Node.js i specyficzne biblioteki.
Czwarte może wymagać przeglądarki, GUI, Playwrighta czy VNC.
Każde środowisko może mieć inną wersję systemu, narzędzi i zależności.
Nie musisz przez to utrzymywać osobnych instalacji OpenHands.

1. Proponowana architektura
OpenHands / Agent Canvas

Interfejs, zarządzanie zadaniami, konfiguracja agentów

Environment Manager

Odczytuje konfigurację repozytorium i wybiera środowisko

Claude

Claude Code CLI

Node / Python

Codex

Codex CLI

Node / Python

Frontend

Playwright / Chrome

VNC / GUI

GPU / ML

CUDA / PyTorch

Python / Conda

Repozytorium + wolumeny + sekrety

Każdy agent pracuje w odizolowanym kontenerze

Ja rozdzieliłbym trzy rzeczy:

Base image – system operacyjny, pakiety, języki, biblioteki, GUI.
Agent – Claude Code, Codex albo inny agent.
Project configuration – zależności konkretnego repozytorium, komendy startowe, testy i zmienne środowiskowe.
Nie tworzyłbym osobnego obrazu dla każdego repozytorium. Lepiej mieć obrazy bazowe wielokrotnego użytku.

2. Konfiguracja per repozytorium
Wprowadziłbym prosty standard, np. .openhands/environment.yaml.

Przykładowa konfiguracja:

yaml

version: 1

environment:
  image: ghcr.io/mycompany/agents/claude-node:22
  # Alternatywnie:
  # image: ghcr.io/mycompany/agents/codex-python:3.12

agent:
  type: claude-code
  # lub: codex

setup:
  commands:
    - npm install
    - npx playwright install --with-deps

runtime:
  working_dir: /workspace
  ports:
    - 3000
    - 5173

  gui:
    enabled: false

  gpu:
    enabled: false
Dzięki temu repozytorium samo deklaruje, czego potrzebuje.

Przykładowo:

Repozytorium	Środowisko	Agent
frontend-app	Node 22 + Playwright	Claude Code
backend-api	Python 3.12 + PostgreSQL client	Codex
ml-project	CUDA + PyTorch	Codex
legacy-app	Java 17 + Maven	Claude Code
browser-automation	Chrome + VNC	Claude Code
To byłaby wasza konwencja konfiguracyjna, którą realizowałby Environment Manager.

3. Jak budować obrazy Docker?
Zrobiłbym katalog z gotowymi obrazami, które można wykorzystywać w wielu projektach.

Przykładowa struktura:

text

agent-environments/
├── base/
│   ├── Dockerfile.common
│   └── scripts/
│       └── install-tools.sh
│
├── claude-node/
│   └── Dockerfile
│
├── codex-python/
│   └── Dockerfile
│
├── browser/
│   └── Dockerfile
│
├── gpu/
│   └── Dockerfile
│
└── docker-compose.yaml
Przykładowy obraz:

dockerfile

FROM node:22-bookworm

# Podstawowe narzędzia
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    python3 \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Claude Code
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /workspace
Analogicznie robicie obraz z Codex CLI:

dockerfile

FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex

WORKDIR /workspace
Ważne: w aktualnym OpenHands V1 nie wystarczy podmienić obrazu na dowolny Docker image. Sandbox jest jednocześnie serwerem Agent Server, więc własny obraz musi zawierać ten komponent. Oficjalna dokumentacja opisuje budowanie własnego obrazu na bazie OpenHands Agent Server.

GitHub

W praktyce przygotowałbym więc własne obrazy bazowe z dodatkowymi narzędziami, a następnie nakładał na nie warstwę Agent Server.

4. A co z GUI, przeglądarką i VNC?
Tutaj Docker również się sprawdzi.

OpenHands ma możliwość budowania obrazów z VS Code i VNC. W dokumentacji opisano również warianty binary oraz binary-minimal.

GitHub

Możecie mieć np.:

agent-base – podstawowe narzędzia programistyczne.
agent-browser – Chrome, Playwright, VNC.
agent-gui – środowisko graficzne.
agent-gpu – CUDA i biblioteki ML.
Nie instalowałbym GUI w każdym obrazie. To niepotrzebnie zwiększa ich rozmiar.

5. Najważniejszy element: Environment Manager
Jest jedna rzecz, którą warto uwzględnić: aktualna konfiguracja własnego obrazu OpenHands V1 przez AGENT_SERVER_IMAGE_REPOSITORY i AGENT_SERVER_IMAGE_TAG jest globalna dla uruchomionej instancji, a nie automatycznie wybierana na podstawie repozytorium.

GitHub

Dlatego do pełnej automatyzacji potrzebujecie niewielkiej warstwy zarządzającej.

Jej zadania:

Klonuje repozytorium.
Odczytuje .openhands/environment.yaml.
Wybiera odpowiedni obraz.
Uruchamia izolowany sandbox z tym obrazem.
Podłącza repozytorium jako /workspace.
Przekazuje sekrety i zmienne środowiskowe.
Uruchamia odpowiedniego agenta.
Sprząta środowisko po zakończeniu zadania.
Warto też rozdzielić konfigurację agenta od obrazu środowiska. Agent może być uruchamiany jako ACP agent, a Agent Canvas obsługuje integracje m.in. z Claude Code i Codex.

GitHub

+1

6. Czy warto użyć Dev Containers?
Moim zdaniem warto rozważyć standard Development Containers (devcontainer.json).

To rozwiązanie jest już wykorzystywane w VS Code, GitHub Codespaces i innych narzędziach.

Przykładowo repozytorium może zawierać:

text

repo/
└── .devcontainer/
    ├── devcontainer.json
    └── Dockerfile
A konfiguracja:

json

{
  "name": "My Project",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "features": {
    "ghcr.io/devcontainers/features/node:1": {
      "version": "22"
    }
  },
  "postCreateCommand": "npm install"
}
Zaletą jest to, że nie wymyślacie własnego standardu konfiguracji środowisk programistycznych.

Możecie stworzyć adapter, który:

Odczytuje devcontainer.json.
Buduje środowisko na jego podstawie.
Dodaje wymaganą warstwę OpenHands Agent Server.
Uruchamia wybranego agenta.
Dokumentacja: [Development Containers Specification](<https://containers.dev/?utm_source=chatgpt.com>).

7. Co konkretnie bym wdrożył?
Nie budowałbym od razu dużego systemu. Zacząłbym od trzech elementów:

Etap 1Registry obrazów

GHCR z kilkoma gotowymi obrazami:

agent-node
agent-python
agent-browser
agent-gpu
Etap 2Environment Manager

Mały serwis w Pythonie lub Go, który:

Odczytuje konfigurację repo.
Wybiera obraz.
Tworzy kontener.
Podłącza workspace.
Uruchamia agenta.
Etap 3Automatyzacja

Cache obrazów.
Automatyczne budowanie obrazów.
Wspólne cache npm/pip.
Limity CPU/RAM/GPU.
Sprzątanie nieaktywnych kontenerów.
Moja rekomendacja: Docker jako warstwa izolacji, Dev Containers jako standard deklarowania środowiska, GHCR jako registry i mały Environment Manager jako integracja z OpenHands.

Jeszcze dwie istotne rzeczy:

Nie współdzielcie kontenerów między niezaufanymi zadaniami. Każde zadanie powinno mieć własny sandbox.
Nie wkładajcie kluczy API do obrazów. Przekazujcie je jako sekrety podczas uruchamiania kontenera.
Jedna ważna decyzja architektoniczna
Chciałbym doprecyzować jedną rzecz, bo od niej zależy najlepszy sposób implementacji:

Czy chcecie, żeby OpenHands automatycznie uruchamiał różne środowiska dla różnych repozytoriów w ramach jednej instancji, bez ręcznego przełączania konfiguracji?

Jeżeli tak, zaprojektowałbym to jako niezależny Environment Manager, który dynamicznie tworzy kontenery i podpina je do OpenHands. To daje największą elastyczność i pozwala później uruchamiać wiele agentów równolegle, każdy w zupełnie innym środowisku.