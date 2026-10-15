# KiCad Library Management Workflow
**2026-08-25**
* A workflow for managing the KiCad libraries
 
## Terminology
* project -- do not use without qualifier
* git project -- directory that contains the .git directory
<br>better to call this directory the repo, or the git repo
* kicad project -- the directory that contains the .kicad_pro file
<br>when KiCad opens a project, it sets variable KIPRJMOD to the .kicad_pro directory

### File and directory names
**.kicad_mod** — a single footprint file (lives inside a .pretty library folder)
<br>**.kicad_pcb** — PCB layout file
<br>**.kicad_pro** — project file (ties everything together, stores project settings)
<br>**.kicad_prl** — project local settings (per-user UI state, e.g. open layers/view — not meant to be shared/version-controlled)
<br>**.kicad_sch** — schematic file
<br>**.pretty** — a footprint library (a folder containing .kicad_mod files)
<br>**sym-lib-table** — index file listing which symbol libraries are available (global or per-project)
<br>**fp-lib-table** — index file listing which footprint libraries are available (global or per-project)
<br>**3D Models** — the name of a tab in the Footprint Properties dialog
<br>**.3dshapes** — only used as dirname extension to indicate directory holds STEP files
<br>**.step** — a 3D model file format (STEP), used for realistic 3D views of parts/board
<br>**.kicad_sym** — a symbol library file (contains one or more schematic symbols)
<br>**-backups/** — folder KiCad auto-creates with zipped backups of your project
<br>**fp-info-cache** — cache file speeding up footprint library browsing (safe to delete/regenerate)

### Target repo structure
* Major flaw:  KiCad defaults to one project file per directory, or each project gets its own directory
* Workaround:  there's a python script (in ./extras/) for setting up these sibling projects that share a directory and share their project specific libraries
* Using notional file names
```text
ESP32_2026-00/                    ← this is the repo name
├── .git/
├── docs/
├── electrical/
│   ├── datasheets/
│   └── pinouts/
├── extras/                       ← KiCad project setup script is here 
├── freecad/
├── kicad/                        ← KiCad env variable is the full pathname to here
│   ├── breadboard.kicad_pro      ← this could be a feasibility version (sibling 0)
│   ├── breadboard.kicad_sch
│   ├── breadboard.kicad_pcb
│   ├── perfboard.kicad_pro       ← this will be the first soldered version (sibling 1)
│   ├── perfboard.kicad_sch
│   ├── perfboard.kicad_pcb
│   ├── receiver.kicad_pro        ← notional sibling project (sibling 2)
│   ├── receiver.kicad_sch
│   ├── transmitter.kicad_pro     ← another notional sibling project (sibling 3)
│   └── transmitter.kicad_sch
│   └── libraries/                ← the KiCad project libraries themselves go here
│       ├── _symbols.kicad_sym    ← contains all the project symbols, maybe more
│       ├── _footprints.pretty/   ← contains at least one footprint for each symbol
│       │   └── *.kicad_mod
│       └── _models/              ← KiCad calls them 3D Models, but don't change it
│           └── *.step
├── LLM_chats/
├── mechanical/
├── shared_lib/                   ← this is a code library that PlatformIO reads
└── sketches/                     ← this contains PlatformIO "projects"
```

## New Project Workflow
* Use the setup script in the extras/ directory.
* Use the workflows in the extras/ directory and in ~/Documents/Workflows/KiCad/

## Set Libraries
#### In the schematic editor
* Preferences > ManageSymbolLibraries
* Note the **two library tabs** 
* Global Libraries (first tab) - typcial choices include
  - **KiCad** -- the library bundled with KiCad
  - **_hobby_parts** -- under *~/Documents/KiCad EDA/HobbyParts/symbols/*
  <br>also include any other libraries under *HobbyParts/symbols/*
  - These library paths must contain absolute system pathnames
  <br>Do **not** use $KIPRJMOD on this tab
* Project Specific Library (second tab) - typcial choices include
  - **_symbols** -- ${KIPRJMOD}/libraries/_symbols.kicad_sym

#### In the library part editor
* Create a new library, **${KIPRJMOD}/libraries/_symbols**, if necessary

