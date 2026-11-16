RoboLab SAFE4
Projeto acadêmico de robótica móvel que simula um robô autônomo (AMR) em um galpão. O robô segue cinco pontos no corredor central, enquanto um nó separado, o Sentry, valida os comandos de velocidade antes de encaminhá-los ao simulador.

[Documentação do projeto](docs/Documentacao_RoboLab.md)
Funcionamento
O Gazebo publica a pose do robô em /odom por meio da ponte ROS 2. O nó waypoint_nav usa a pose para calcular o movimento, o Sentry verifica os limites do comando e o controlador DiffDrive aplica a velocidade às rodas. O LiDAR simulado tem publicação configurada em /scan para inspeção. O percurso segue pontos predefinidos com base na odometria.

O mundo padrão, warehouse_blender.sdf, inclui as malhas do galpão e do AMR. O galpão foi ajustado a 25% da escala original, aberto no topo para facilitar a visualização e alinhado ao corredor da rota. As colisões das estruturas são aproximadas. As juntas das rodas usam o referencial do chassi, com o eixo transversal em Y e a frente em +X. Dois apoios inferiores de baixo atrito limitam a inclinação do robô.
Estrutura
Caminho	Conteúdo
ros2_ws/src/amr_security_lab/	Nós Python, launch, mundos SDF, malhas OBJ e materiais MTL
tests/	Testes automatizados
windows_demo/	Demonstração 2D em Python e Tkinter
site/	Painel RoboLab com diário do projeto e página de realidade aumentada
ar/	Demonstração de realidade aumentada com o marcador Hiro
docs/	Documentação do projeto


Executar no Gazebo
O ambiente usado pelo projeto é Ubuntu 24.04 com ROS 2 Jazzy, Gazebo Harmonic, ros_gz e colcon. No Windows, execute a simulação pelo Ubuntu no WSL2. Para instalar o ROS 2, siga a documentação do Jazzy.

Na raiz do projeto, dentro do Ubuntu, compile o workspace na primeira execução ou após alterar arquivos instalados:
cd ros2_ws &&
source /opt/ros/jazzy/setup.bash &&
colcon build --symlink-install
Terminal 1 · Abrir o galpão e iniciar a ponte e o Sentry
cd ros2_ws &&
source /opt/ros/jazzy/setup.bash &&
source install/setup.bash &&
ros2 launch amr_security_lab security_lab.launch.py
Terminal 2 · Iniciar a rota

Com o Gazebo em Play, abra outro terminal na raiz do projeto:
cd ros2_ws &&
source /opt/ros/jazzy/setup.bash &&
source install/setup.bash &&
ros2 run amr_security_lab waypoint_nav
Para abrir o cenário alternativo, acrescente world:=warehouse.sdf ao comando de launch. Para acompanhar a simulação, abra outro terminal com o mesmo ambiente ROS 2 carregado e execute um comando de cada vez:
ros2 topic echo /odom --once
ros2 topic echo /scan --once --qos-reliability best_effort
ros2 topic echo /security_status
O painel ROS 2 pode ser iniciado com ros2 run amr_security_lab dashboard em um ambiente com Tkinter e interface gráfica disponíveis. A demonstração 2D para Windows pode ser aberta com INICIAR_WINDOWS.bat e roda de forma independente.
Realidade aumentada
Abra a página Realidade aumentada no painel, permita o acesso à câmera pelo navegador do celular e aponte para o marcador Hiro em outra tela ou impresso. A demonstração usa o modelo 3D do AMR e pode ser aberta pelo link HTTPS do painel.
Testes e validação
Na raiz do projeto, execute:
python3 -m unittest discover -s tests -v
Na versão corrigida, os 19 testes automatizados passaram. As evidências anteriores registram odometria, aceitação de um comando dentro dos limites e bloqueio de um comando angular fora do limite pelo Sentry. A validação prática da versão corrigida inclui conferir o sentido do avanço no Gazebo, registrar uma leitura do LiDAR e testar a realidade aumentada no celular.
