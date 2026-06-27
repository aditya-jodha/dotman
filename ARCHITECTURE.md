# Architecture

Dotman is divided into three layers 



- Core components:

  | File                    | Purpose                                                       |
  | ----------------------- | ------------------------------------------------------------- |
  | `linker.py`             | Linking & unlinking files                                     |
  | `add.py`                | Add files to dotfiles folder                                  |
  | `doctor.py`             | Verify symlink, dotfiles, homedir health                      |
  | `profile.py`            | Manage profiles: get, create, delete                          |
  | `get_internal_data.py`  | Get internal data (e.g. current_profile from metadata.yml)    |
  | `config.py`             | Handle configurations (dotfiles folder name, etc)             |

```mermaid
  flowchart TD
    %% Styling Definitions
    classDef coreHub fill:#581c44,stroke:#8a2f6b,stroke-width:3px,color:#fff,font-weight:bold;
    classDef componentStyle fill:#2c1826,stroke:#663859,stroke-width:2px,color:#fff;
    classDef wrapperBox fill:#1a0e17,stroke:#4a2840,stroke-width:2px,stroke-dasharray: 5 5,color:#cbd5e1;

    subgraph Core_System ["📦 Core System Modules"]
        direction TB
        core((Core Engine))
        
        %% Component Nodes
        linker[<b>linker.py</b><br><i>Linking & unlinking files</i>]
        add[<b>add.py</b><br><i>Add files to dotfiles folder</i>]
        doctor[<b>doctor.py</b><br><i>Verify symlink, dotfiles & homedir health</i>]
        profile[<b>profile.py</b><br><i>Manage profiles: get, create, delete</i>]
        internal[<b>get_internal_data.py</b><br><i>Get data from metadata.yml</i>]
        config[<b>config.py</b><br><i>Handle configurations & folder names</i>]
    end

    %% Apply Styles
    class core coreHub;
    class linker,add,doctor,profile,internal,config componentStyle;
    class Core_System wrapperBox;

    %% Connections
    core --> linker
    core --> add
    core --> doctor
    core --> profile
    core --> internal
    core --> config

```

- Service layer: (works as a Orchestration layer)

  | File                    | Purpose                                                         |
  | ----------------------- | --------------------------------------------------------------- |
  | `profile_service.py`    | Connects CLI profile commands → core `profile.py` + `linker.py` |
  | `doctor_service.py`     | Connects CLI doctor command → core `doctor.py`                  |
  | `add_service.py`        | Connects CLI add command → core `add.py`                        |
  | `remove_service.py`     | Connects CLI remove command → standard `pathlib.Path`           |
  | `sync_service.py`       | Connects CLI sync command → core `linker.py`                    |
  | `initializer_service.py`| Connects CLI init command → core `config.py`                    |

```mermaid
    flowchart LR
    %% Styling Definitions
    classDef cliNode fill:#2b3a4a,stroke:#3a4f66,stroke-width:2px,color:#fff;
    classDef serviceNode fill:#1e4620,stroke:#2d6630,stroke-width:2px,color:#fff;
    classDef coreNode fill:#4a2840,stroke:#663859,stroke-width:2px,color:#fff;
    classDef stdLib fill:#444,stroke:#666,stroke-width:2px,color:#fff;

    %% 1. CLI Layer (User Entry Point)
    subgraph CLI_Zone ["💻 CLI Commands (Entry Point)"]
        CLI_Doctor(doctor)
        CLI_Profile(profile)
        CLI_Add(add)
        CLI_Remove(remove)
        CLI_Sync(sync)
        CLI_Init(init)
    end
    class CLI_Doctor,CLI_Profile,CLI_Add,CLI_Remove,CLI_Sync,CLI_Init cliNode;

    %% 2. Service Layer (Orchestration Engine)
    subgraph Service_Zone ["⚙️ Service Layer (Orchestrator)"]
        doctor_srv(doctor_service.py)
        profile_srv(profile_service.py)
        add_srv(add_service.py)
        remove_srv(remove_service.py)
        sync_srv(sync_service.py)
        init_srv(initializer_service.py)
    end
    class doctor_srv,profile_srv,add_srv,remove_srv,sync_srv,init_srv serviceNode;

    %% 3. Core & Dependencies Layer (Execution Targets)
    subgraph Core_Zone ["📦 Core & Standard Lib (Execution)"]
        doctor_core(doctor.py)
        profile_core(profile.py)
        linker_core(linker.py)
        add_core(add.py)
        config_core(config.py)
        pathlib_std[pathlib.Path]
    end
    class doctor_core,profile_core,linker_core,add_core,config_core coreNode;
    class pathlib_std stdLib;

    %% --- Corrected Connection Flow ---
    %% CLI triggers the Orchestrator, which delegates to Core
    CLI_Doctor  -->|routes to| doctor_srv  -->|executes| doctor_core
    
    CLI_Profile -->|routes to| profile_srv -->|executes| profile_core
    profile_srv -->|resolves| linker_core
    
    CLI_Add     -->|routes to| add_srv     -->|executes| add_core
    
    CLI_Remove  -->|routes to| remove_srv  -->|calls| pathlib_std
    
    CLI_Sync    -->|routes to| sync_srv    -->|executes| linker_core
    
    CLI_Init    -->|routes to| init_srv    -->|updates| config_core

```

  > This separation keeps business logic independent from CLI commands.

- Overall architecture:

```mermaid
    flowchart TB
        %% Styling Definitions
        classDef cliStyle fill:#2b3a4a,stroke:#3a4f66,stroke-width:2px,color:#fff;
        classDef serviceStyle fill:#1e4620,stroke:#2d6630,stroke-width:2px,color:#fff;
        classDef coreStyle fill:#4a2840,stroke:#663859,stroke-width:2px,color:#fff;
        
        classDef cliBox fill:#1a232c,stroke:#3a4f66,stroke-width:2px,stroke-dasharray: 5 5,color:#cbd5e1;
        classDef serviceBox fill:#112913,stroke:#2d6630,stroke-width:2px,stroke-dasharray: 5 5,color:#cbd5e1;
        classDef coreBox fill:#2c1826,stroke:#663859,stroke-width:2px,stroke-dasharray: 5 5,color:#cbd5e1;

        %% ----------------------------------------------------
        %% Top-level blocks
        %% ----------------------------------------------------
        subgraph CLI["💻 Command-Line Interface (CLI Layer)"]
            CLI_Profile(profile command)
            CLI_Doctor(doctor command)
            CLI_Add(add command)
            CLI_Remove(remove command)
            CLI_Sync(sync command)
            CLI_Init(init command)
        end
        class CLI cliBox;
        class CLI_Profile,CLI_Doctor,CLI_Add,CLI_Remove,CLI_Sync,CLI_Init cliStyle;

        subgraph Services["⚙️ Service Layer (Orchestration)"]
            profile_service(profile_service.py)
            doctor_service(doctor_service.py)
            add_service(add_service.py)
            remove_service(remove_service.py)
            sync_service(sync_service.py)
            init_service(initializer_service.py)
        end
        class Services serviceBox;
        class profile_service,doctor_service,add_service,remove_service,sync_service,init_service serviceStyle;

        subgraph Core["📦 Core Layer"]
            profile_core(profile.py)
            doctor_core(doctor.py)
            add_core(add.py)
            linker_core(linker.py)
            initalizer_core(initalizer.py)
        end
        class Core coreBox;
        class profile_core,doctor_core,add_core,linker_core,initalizer_core coreStyle;

        %% ----------------------------------------------------
        %% Connections
        %% ----------------------------------------------------
        CLI_Profile -->|calls| profile_service
        profile_service -->|executes| profile_core
        profile_service -->|resolves via| linker_core

        CLI_Doctor -->|calls| doctor_service
        doctor_service -->|executes| doctor_core

        CLI_Add -->|calls| add_service
        add_service -->|executes| add_core

        CLI_Remove -->|calls| remove_service

        CLI_Sync -->|calls| sync_service
        sync_service -->|links via| linker_core

        CLI_Init -->|calls| init_service
        init_service --> initalizer_core

```

    > Note:
    <br>
    > - Config command is not shown in the diagram.
    <br>
    > - Some basic things like calling std lib like pathlib typer and some inbuild modules like calling config is not shown in the diagram.