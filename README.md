# Cyber-Physical AMR Security Lab

[Documentação do projeto e guia de publicação no Git](docs/Documentacao_RoboLab.md)

## Correção de movimento do AMR

Os eixos das rodas foram declarados no referencial do chassi, com eixo transversal
`Y` e avanço em `+X`. O robô ganhou dois apoios inferiores de baixo atrito.
O apoio traseiro fica na altura de contato das rodas e o dianteiro tem uma folga
de 2 mm. Eles limitam a inclinação para evitar que o chassi arraste no piso.

Recompile o workspace extraído conforme a seção 3. Abra o launch e inicie
`waypoint_nav` em outro terminal. No primeiro trecho, confira se a barra azul
da frente aponta na direção do movimento. Se o robô ainda aparentar andar de lado,
compare a vista do Gazebo com a posição e a orientação em `/odom`.
A versão foi conferida estaticamente. A movimentação requer teste no Gazebo Harmonic.

A pasta `ar` contém a demonstração para StackBlitz com o marcador Hiro.

## Abrir a versão com o galpão Blender

O launch padrão abre `warehouse_blender.sdf`, inicia a ponte ROS 2 e o Sentry.
O galpão foi reduzido a 25%, alinhado ao corredor da rota e aberto no topo para facilitar
a câmera. As colisões das estruturas são aproximadas. A carroceria aponta para +X e
as duas rodas visuais acompanham os links do DiffDrive. Para abrir o mundo anterior,
use `ros2 launch amr_security_lab security_lab.launch.py world:=warehouse.sdf`.

Após copiar e compilar o projeto conforme a seção 3, abra o launch em um terminal.
Em outro terminal com o mesmo ambiente ROS 2 carregado, verifique:

```bash
ros2 topic echo /odom --once
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 run amr_security_lab waypoint_nav
```

Para receber o scan, mantenha a simulação rodando. O LiDAR GPU usa Ogre 2 no Gazebo.
A navegação segue a odometria. O LiDAR serve para leitura e inspeção, e a validação
da rota e do sensor deve ser feita no Gazebo da equipe.


Protótipo acadêmico para demonstrar navegação de um AMR, injeção controlada de comandos e mitigação por um sentinela. O projeto inclui:
- **Demo local para Windows** (Python + Tkinter): demonstração executável rápida da lógica, ataque e bloqueio.
- **Pacote ROS 2 + Gazebo**: integração em validação para executar no Ubuntu 24.04 via WSL2, com o robô diferencial no Gazebo e o sentinela filtrando comandos.

> **Importante:** Gazebo e ROS 2 não são suportados de forma nativa e simples no Windows. Para cumprir o requisito acadêmico de Gazebo, use Ubuntu 24.04 no WSL2 com ROS 2 Jazzy e Gazebo Harmonic. A demo Windows é um teste rápido complementar, não substitui a demonstração Gazebo.

## 1. Estrutura

```text
DEMO_ROBO_GAZEBO_BLENDER/
├── windows_demo/                 # Interface 2D em Python
├── ros2_ws/src/amr_security_lab/
│   ├── amr_security_lab/        # waypoint_nav.py, sentry.py, attack_demo.py, dashboard.py
│   ├── launch/security_lab.launch.py
│   ├── worlds/warehouse_blender.sdf e worlds/meshes/
│   ├── worlds/warehouse.sdf     # Mundo 3D atualizado pela equipe
│   ├── package.xml
│   └── setup.py
├── tests/                        # Testes Python
├── EVIDENCIAS_DOS_TESTES/        # Evidências históricas
├── INICIAR_WINDOWS.bat
└── TESTAR_WINDOWS.bat
```

O cenário Blender traz as estantes, a sinalização, as áreas de carga e o robô diferencial `amr`. O mundo anterior contém quatro estantes. O percurso ROS 2 continua com **cinco waypoints** ao longo de `y=0`. A demo 2D tem representação própria, não é uma cópia visual exata do SDF.

## 2. Executar a demo no Windows

Requisitos: Python 3.10+ (3.11 recomendado). Tkinter normalmente já vem com o Python oficial para Windows.

1. Extraia o ZIP.
2. Abra a pasta `windows_demo` no VS Code.
3. No terminal:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python amr_security_demo.py
```

A interface inicia em modo normal. Clique em **Iniciar ataque** para simular comandos não autorizados. O sentinela bloqueia velocidades acima do limite e mudanças bruscas de velocidade; clique em **Parar ataque** para retornar ao modo normal. Use **Resetar** para reiniciar a demonstração.

Não precisa instalar bibliotecas externas para a demo Windows.

## 3. Configurar Gazebo + ROS 2 no Windows via WSL2

### 3.1 Instalar WSL2
Abra o PowerShell como administrador:

```powershell
wsl --install -d Ubuntu-24.04
```

Reinicie se solicitado e abra Ubuntu pelo menu Iniciar. Dentro do Ubuntu, atualize:

```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2 Instalar ROS 2 Jazzy e Gazebo Harmonic
Siga a documentação oficial atual para instalar ROS 2 Jazzy no Ubuntu 24.04:
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

Instale integração com Gazebo e ferramentas:

```bash
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-geometry-msgs \
  ros-jazzy-rclpy python3-colcon-common-extensions
```

Em cada terminal Ubuntu:

```bash
source /opt/ros/jazzy/setup.bash
```

### 3.3 Copiar o projeto para WSL
A pasta extraída no Windows costuma estar acessível por `/mnt/c/Users/SEU_USUARIO/Downloads/`. Copie o workspace para o diretório home do Ubuntu (substitua o caminho):

```bash
mkdir -p ~/projeto_robo_atualizado
# Substitua SEU_USUARIO pelo usuário do Windows e confira onde extraiu o ZIP.
cp -r "/mnt/c/Users/SEU_USUARIO/Downloads/DEMO_ROBO_GAZEBO_BLENDER/." ~/projeto_robo_atualizado/
cd ~/projeto_robo_atualizado/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

### 3.4 Executar o pacote
Em um terminal Ubuntu:

```bash
source /opt/ros/jazzy/setup.bash
source ~/projeto_robo_atualizado/ros2_ws/install/setup.bash
ros2 launch amr_security_lab security_lab.launch.py
```

Em outro terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/projeto_robo_atualizado/ros2_ws/install/setup.bash
ros2 run amr_security_lab attack_demo
```

O segundo comando envia, em sequência, comandos seguros e comandos fora do limite ao tópico `/cmd_vel_untrusted`. O sentinela publica apenas os comandos aprovados em `/cmd_vel`. A ponte Gazebo/ROS encaminha `/cmd_vel` ao controlador diferencial do modelo.

### 3.5 Inspecionar tópicos
```bash
ros2 topic list
ros2 topic echo /security_status
ros2 topic echo /cmd_vel
ros2 topic echo /cmd_vel_untrusted
```

Se o mundo abrir mas o robô não responder, confirme que os tópicos Gazebo correspondem aos tópicos configurados no bridge e consulte:
```bash
gz topic -l
ros2 topic list
```
A nomenclatura de tópicos pode variar entre versões de plugins/bridge. O bridge está declarado no launch e deve ser validado no computador da equipe antes da gravação final.

## 4. Como demonstrar os cinco requisitos

1. **Problema real:** armazém automatizado; comandos não autorizados podem causar parada ou movimento inseguro.
2. **IMR no Gazebo:** robô diferencial no mundo `warehouse_blender.sdf`; demonstre movimento e obstáculos. A navegação por waypoints usa odometria; não há desvio automático de obstáculos. Se exigido, integrar Nav2 e sensores simulados.
3. **Integração interdisciplinar:** sentinela em Python, teste de injeção controlado, dashboard/telemetria e evidências da disciplina parceira.
4. **Protótipo executável:** demo Windows e pacote ROS 2/Gazebo.
5. **Reprodutibilidade:** este README, arquitetura, testes e vídeo no repositório GitHub.

**Atenção ao escopo:** a versão inicial contém um robô diferencial e controle seguro de velocidade; não declara Nav2 completo. O nó de waypoints já existe; se o professor exigir desvio dinâmico de obstáculos, será necessário adicionar sensores e planejamento de trajetória (por exemplo, Nav2). Não apresentem a demo local Tkinter como se fosse a simulação Gazebo.

## 5. Evidências a gravar
- vídeo 1: robô no Gazebo movendo-se com comandos seguros;
- vídeo 2: teste de injeção no ambiente isolado e comportamento antes da mitigação;
- vídeo 3: sentinela bloqueando comando inválido e status mudando para `ATTACK_BLOCKED`;
- captura de `ros2 topic echo /security_status`;
- resultados dos testes e versão de ROS 2/Gazebo usados.

## 6. GitHub
Crie um repositório público/privado, copie os arquivos, depois:

```bash
git init
git add .
git commit -m "Initial Cyber-Physical AMR Security Lab prototype"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

Nunca incluam credenciais, chaves privadas ou dados reais da empresa no repositório.

## 7. Navegação automática e dashboard ROS 2

Depois de executar `ros2 launch amr_security_lab security_lab.launch.py`, em outro terminal Ubuntu com os `source` executados:

```bash
ros2 run amr_security_lab waypoint_nav
```

O nó usa `/odom` para navegar automaticamente entre cinco waypoints ao longo do corredor central (y=0). O LiDAR simulado publica em `/scan` no mundo Blender. A navegação usa apenas odometria para seguir os pontos e não implementa desvio de obstáculos ou Nav2. Para testar o ataque, pare o nó de waypoints com Ctrl+C e execute `ros2 run amr_security_lab attack_demo` (não execute os dois simultaneamente).

Para abrir o painel ROS (WSLg e Tkinter devem estar disponíveis):

```bash
sudo apt install -y python3-tk
ros2 run amr_security_lab dashboard
```

**Estado da validação:** arquivos gerados e sintaxe verificada localmente; ROS 2, WSL2 e Gazebo não estão disponíveis neste ambiente de criação, portanto a execução física da simulação ainda precisa ser testada no computador da equipe. O sentinela valida limites físicos, mas **não autentica o publicador**; a injeção é um teste controlado de integridade dos comandos, não uma exploração real de rede nem prova de mitigação de todos os ataques. Um publicador que contorne o sentinela e publique diretamente em `/cmd_vel` não é bloqueado. Para um laboratório de segurança de rede completo, adicionar controle de acesso ROS 2/SROS2 e isolamento de rede.


## SAFE 4 — melhorias adicionadas ao código original

Esta edição preserva o projeto **DEMO ROBO** e acrescenta indicadores no painel Windows, exportação de eventos CSV, testes adicionais e documentos `docs/SAFE4_*.md`.

No Windows (Python 3 com Tkinter):

```powershell
python -m windows_demo.amr_security_demo
python -m unittest discover -s tests -v
```

Ou use `INICIAR_WINDOWS.bat` e `TESTAR_WINDOWS.bat`.

**A demonstração Windows é local e não está conectada ao ROS/Gazebo.**


## Integração Fases 2 e 3
Consulte `docs/INTEGRACAO_FASE2_FASE3.md` para detalhes, execução e limitações.
