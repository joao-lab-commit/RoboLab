# RoboLab SAFE4 — Documentação do projeto

Projeto acadêmico de robótica móvel da Ciência da Computação. O protótipo simula um robô móvel autônomo (AMR) que percorre cinco pontos em um galpão e valida os comandos de velocidade antes de enviá-los ao simulador.

## Arquitetura

| Componente | Função |
|---|---|
| Ubuntu 24.04 no WSL2 | Ambiente de desenvolvimento e execução |
| Gazebo Harmonic e SDF | Mundo 3D, física, colisões, rodas e sensor simulado |
| Blender | Modelos visuais do AMR e do galpão, incorporados ao Gazebo em OBJ/MTL |
| ROS 2 Jazzy e Python | Comunicação entre nós, navegação por waypoints e validação de comandos |
| Site RoboLab | Roteiro, diagnóstico e diário com registros locais no navegador |
| A-Frame e AR.js | Exibição do modelo GLB do AMR sobre o marcador Hiro pela câmera do celular |

O Gazebo fornece a odometria pelo tópico `/odom` via ponte. O nó `waypoint_nav` lê a pose e usa um timer para enviar velocidades calculadas a `/cmd_vel_untrusted`. O `sentry` valida os limites dos comandos de movimento, envia a saída para `/cmd_vel` e publica o estado da validação em `/security_status`. A ponte leva a velocidade ao DiffDrive no Gazebo. O LiDAR simulado tem publicação configurada em `/scan` e pode ser inspecionado separadamente. A rota usa odometria e waypoints predefinidos.

## Executar a simulação

Pré-requisitos no Ubuntu/WSL2: ROS 2 Jazzy, Gazebo Harmonic, integração `ros_gz` e `colcon`. O `README.md` detalha a instalação.

No primeiro terminal, a partir da raiz do repositório:

```bash
cd ros2_ws &&
source /opt/ros/jazzy/setup.bash &&
colcon build --symlink-install &&
source install/setup.bash &&
ros2 launch amr_security_lab security_lab.launch.py
```

No segundo terminal, também a partir da raiz do repositório, com o Gazebo em Play:

```bash
cd ros2_ws &&
source /opt/ros/jazzy/setup.bash &&
source install/setup.bash &&
ros2 run amr_security_lab waypoint_nav
```

Para inspecionar, rode `ros2 topic echo /odom --once` e `ros2 topic echo /scan --once --qos-reliability best_effort` em outro terminal com o ambiente carregado. Para abrir o cenário anterior, acrescente `world:=warehouse.sdf` ao comando de launch.

## Testes e estado atual

- **Testes automatizados:** 19 testes passaram na versão corrigida. Execute `python3 -m unittest discover -s tests -v` na raiz. A suíte cobre lógica da demo, navegação, política de velocidade e consistência dos mundos.
- **Evidências anteriores:** o projeto tem registros históricos de odometria e do Sentry aceitando um comando válido e bloqueando um comando angular fora do limite. Esses registros pertencem às sessões anteriores à correção.
- **Correção do movimento:** os eixos das rodas passaram a ser expressos em relação ao chassi, e dois apoios inferiores de baixo atrito limitam a inclinação. Ainda é preciso confirmar no Gazebo se, ao percorrer a rota, a barra azul aponta no sentido do deslocamento.
- **Validação prática:** registrar a rota no galpão atualizado, uma leitura do LiDAR e uma captura da AR no celular. Os testes automatizados não reproduzem a física do Gazebo nem o rastreamento pela câmera.

## Relação com Paradigmas de Programação

O projeto usa orientação a objetos nos nós Python e programação orientada a eventos nos callbacks acionados por mensagens e timers. Tópicos desacoplam o simulador, a navegação e a validação de velocidade. A organização em simulação, controle, políticas, painel e AR permite testar cada parte e manter as interfaces de comunicação explícitas.

## O que subir no GitHub

Use como raiz a pasta extraída `RoboLab_Repositorio`. Suba os itens que estão dentro dela:

| Caminho | O que contém |
|---|---|
| `README.md` e `docs/Documentacao_RoboLab.md` | Instruções de execução e documentação |
| `ros2_ws/src/amr_security_lab/` | Pacote ROS 2 inteiro, incluindo launch, SDF, OBJ e MTL |
| `tests/` | Testes automatizados |
| `windows_demo/`, `INICIAR_WINDOWS.bat` e `TESTAR_WINDOWS.bat` | Demo auxiliar para Windows |
| `site/` | Arquivos do painel e da demonstração AR usados na hospedagem |
| `ar/` | Demonstração AR separada, pronta para reutilizar no StackBlitz |
| `.gitignore` | Exclusões de arquivos gerados e configurações locais |

Envie os arquivos extraídos. Deixe fora do Git os ZIPs, `build/`, `install/`, `log/`, caches Python e credenciais. O pacote para o Git deixa os prints e logs históricos na entrega privada existente. Para compartilhar essas evidências com o professor, revise-as primeiro e envie pelo canal escolhido pelo grupo.

