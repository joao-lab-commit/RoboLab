const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const key = 'robolab-v1';
const labels = [['visao','◈','Visão geral'],['execucao','▸','Execução'],['comandos','›_','Comandos'],['diagnostico','⌁','Diagnóstico'],['integracao','▧','Integração 3D'],['ar','◎','Realidade aumentada'],['paradigmas','{}','Paradigmas'],['diario','▤','Diário do projeto']];
const checks = ['Ubuntu aberto e distribuição ROS 2 confirmada','Workspace carregado em cada terminal','Mundo e robô carregados no Gazebo','Bridge ativa e tópicos corretos identificados','LiDAR publica leituras em /scan (ou equivalente)','Avanço e rotação testados separadamente'];
const phases = ['A validar','Em andamento','Validado','Bloqueado'];
const kinds = ['Alteração no código','Teste','Print','Pendência','Próximo passo'];
const statuses = ['Pendente','Em andamento','Concluído','Aprovado','Falhou'];
const initial = {checks:[], records:[], commands:[], phase:phases[0], ws:'', distro:'', world:'', pkg:'', launch:''};
let state;
try { state = {...initial, ...JSON.parse(localStorage.getItem(key) || '{}')}; } catch { state = {...initial}; }
const allRecords = () => {
  const localIds = new Set(state.records.map(record => record.id));
  return [...state.records, ...historicoProjeto.filter(record => !localIds.has(record.id))]
    .sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
};
let toastTimer, editId, filter = '', search = '';
function toast(message) { $('#toast').textContent=message; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#toast').textContent='',3600); }
function save(patch) {
  const next = {...state,...patch};
  try { localStorage.setItem(key, JSON.stringify(next)); }
  catch { toast('Sem espaço disponível ou armazenamento bloqueado. Exporte um backup ou use um print menor.'); return false; }
  state=next; return true;
}
const quote = (s) => "'" + s.replaceAll("'", "'\"'\"'") + "'";
const path = (s, fallback) => !s ? fallback : s.startsWith('~/') ? '"$HOME"/'+quote(s.slice(2)) : quote(s);
function commands() {
  const ws=path(state.ws,'"$HOME/ros2_ws"'), world=path(state.world,'"$HOME/ros2_ws/src/<caminho>/warehouse.sdf"');
  const overlay='cd -- '+ws+'\nsource install/setup.bash';
  return {
    integrated:'source /opt/ros/jazzy/setup.bash &&\nsource ~/DEMO_ROBO_GAZEBO_BLENDER/ros2_ws/install/setup.bash &&\nros2 launch amr_security_lab security_lab.launch.py',
    route:'source /opt/ros/jazzy/setup.bash &&\nsource ~/DEMO_ROBO_GAZEBO_BLENDER/ros2_ws/install/setup.bash &&\nros2 run amr_security_lab waypoint_nav',
    os:'cat /etc/os-release\nls /opt/ros\ncommand -v gz; command -v ign',
    setup:'source /opt/ros/'+(state.distro ? quote(state.distro) : '<distro>')+'/setup.bash\nprintf "%s\\n" "$ROS_DISTRO"\n'+overlay,
    build:'cd -- '+ws+'\ncolcon build --symlink-install\nsource install/setup.bash',
    launch:'ros2 launch '+(state.pkg?quote(state.pkg):'<pacote>')+' '+(state.launch?quote(state.launch):'<arquivo.launch.py>'),
    gazebo:'gz sim -r '+world,
    topics:'ros2 node list\nros2 topic list -t\ngz topic -l',
    lidar:'ros2 topic info /scan -v\nros2 topic echo /scan --once --qos-reliability best_effort\nros2 topic hz /scan',
    drive:'ros2 topic info /cmd_vel -v\nros2 topic type /cmd_vel\nros2 topic echo /odom --once',
    forward:"timeout 3s ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.2}}'\nros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'",
    rotate:"timeout 3s ros2 topic pub -r 5 /cmd_vel geometry_msgs/msg/Twist '{angular: {z: 0.4}}'\nros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist '{}'",
    bridge:"ros2 run ros_gz_bridge parameter_bridge '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan' '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist'",
    test:'colcon test --packages-select '+(state.pkg?quote(state.pkg):'<pacote>')+'\ncolcon test-result --verbose',
  };
}
const examples = {os:'Identificar ambiente',setup:'Carregar ROS 2 e workspace',build:'Compilar workspace',launch:'Iniciar projeto pelo launch',gazebo:'Abrir mundo isolado',topics:'Inspecionar nós e tópicos',lidar:'Validar LiDAR',drive:'Inspecionar movimento',forward:'Testar avanço',rotate:'Testar rotação',bridge:'Iniciar bridge mínima',test:'Rodar testes do pacote'};
const issues = [
 ['parado','Robô parado','Atuação','Confirme o botão Play do Gazebo e que o robô apareceu com as rodas em contato com o chão. Confira se /cmd_vel tem assinante e se há um controlador ativo ou plugin DiffDrive carregado. Desative o nó autônomo antes de testar um comando isolado em simulação. Se o tópico exige TwistStamped, ajuste o publicador para esse tipo. Compare a pose no Gazebo e a odometria antes/depois.','drive'],
 ['giro','Rodas giram, robô gira no lugar','Cinemática','Envie avanço com linear.x > 0 e angular.z = 0. Se o chassi gira, compare os joints esquerdo e direito, eixos locais e sinais no modelo; as duas rodas devem produzir avanço no mesmo sentido no referencial do chassi. Se as rodas giram e o chassi fica no lugar, verifique colisões, atrito e contato com o piso.','forward'],
 ['lateral','Robô se move de lado','Referenciais','Para tração diferencial, teste apenas linear.x e verifique linear.y = 0. Confira se a frente de base_link aponta para +X, os eixos de rotação das rodas e a orientação dos links em relação ao chassi. Se o movimento físico está correto com a aparência de lado, confira a rotação da malha visual do chassi.','forward'],
 ['topicos','Tópicos sem publicação','Comunicação','Compare as listas de ROS 2 e Gazebo Transport. Se o sensor existe só no Gazebo, revise nomes, namespace, tipo e direção da bridge. Se há publicador ROS sem dados no echo, confira a simulação em execução, QoS e ROS_DOMAIN_ID entre terminais. Se nem o tópico Gazebo aparece, revise a configuração do sensor e do sistema de sensores no mundo.','topics']
];
const shell = (id) => '<div class="terminal"><div class="row"><span>TERMINAL · BASH</span><button data-copy="'+id+'">Copiar</button></div><pre>'+escapeHtml(commands()[id])+'</pre></div>';
const head = (title, description) => '<div class="section-head"><h1>'+title+'</h1><p>'+description+'</p></div>';
const card = (title, body) => '<section class="card"><h2>'+title+'</h2>'+body+'</section>';
const options = (values, selected) => values.map(v=>'<option'+(v===selected?' selected':'')+'>'+escapeHtml(v)+'</option>').join('');
const checklist = () => '<progress max="'+checks.length+'" value="'+state.checks.length+'" aria-label="Progresso da execução"></progress>'+checks.map((item,index)=>'<label class="check"><input type="checkbox" data-check="'+index+'" '+(state.checks.includes(index)?'checked':'')+'>'+item+'</label>').join('');
const pages = {
 visao() {
   const pending = allRecords().filter(r=>['Pendência','Próximo passo'].includes(r.kind)&&['Pendente','Em andamento','Falhou'].includes(r.status)).length;
   return '<section class="hero"><img src="galpao.webp" alt="" aria-hidden="true"><div class="hero-copy"><span class="kicker">Operação e validação</span><h1>Robô no galpão</h1><p>Controle o roteiro de simulação, valide o movimento e documente o que mudou no projeto.</p><a class="primary action" href="#execucao">Abrir roteiro de execução →</a><div class="badges">'+['ROS 2','Gazebo','Ubuntu','Python','LiDAR','Blender'].map(v=>'<span class="badge">'+v+'</span>').join('')+'</div></div></section>'+
   '<div class="stats">'+[['Execução',state.checks.length+' / '+checks.length,'etapas marcadas'],['Pendências',pending,'registros abertos'],['Testes',allRecords().filter(r=>r.kind==='Teste').length,'resultados registrados']].map(([a,b,c])=>'<section class="card stat"><span class="kicker">'+a+'</span><strong>'+b+'</strong><small>'+c+'</small></section>').join('')+'</div>'+
   '<div class="grid">'+card('Checklist de execução',checklist())+card('Diagnóstico rápido',issues.map(([id,title,tag])=>'<a class="issue" href="#diagnostico/'+id+'"><span>'+title+'</span><span class="kicker">'+tag+' ↗</span></a>').join(''))+'</div>'+
   '<div class="project-state">'+card('Estado do projeto','<label class="status-select">Situação da validação<select id="phase">'+options(phases,state.phase)+'</select></label><p>O launch abre o AMR no galpão do Blender com LiDAR configurado em /scan. A suíte local registrou 18 testes aprovados. O diário reúne as evidências anteriores e as validações pendentes da rota, do LiDAR e da AR.</p><a href="#diario">Abrir diário do projeto →</a>')+'</div>';
 },
 execucao() {
   const field = (name,label,placeholder) => '<label>'+label+'<input name="'+name+'" value="'+escapeHtml(state[name])+'" placeholder="'+placeholder+'"></label>';
   return head('Execução','Abra o Ubuntu e mantenha simulador, controle e inspeção em terminais separados.')+'<div class="stack">'+
   card('Configuração da sua máquina','<p>Preencha os valores reais do projeto para gerar os comandos. Os valores entre &lt; &gt; são marcadores. O caminho ~/ros2_ws é um exemplo. Os comandos gz usam Gazebo Sim moderno. Se seu ambiente usa Fortress, verifique os equivalentes ign gazebo e ign topic.</p><form id="config"><div class="grid">'+field('ws','Workspace','~/ros2_ws')+field('distro','Distribuição ROS 2','jazzy')+field('world','Caminho do mundo SDF','~/ros2_ws/src/.../warehouse.sdf')+field('pkg','Pacote ROS 2','Nome do pacote')+field('launch','Arquivo launch','simulacao.launch.py')+'</div><button class="primary">Salvar configuração</button></form>')+
   card('Atalho do projeto integrado','<p>Após compilar o ZIP DEMO_ROBO_GAZEBO_BLENDER, carregue o ambiente em cada terminal. Deixe o launch aberto, coloque o Gazebo em Play e inicie a rota no segundo terminal.</p>'+shell('integrated')+shell('route'))+
   card('Antes de abrir a simulação','<p>Inicialize a instalação ou VM Ubuntu, confirme a distribuição ROS 2 e carregue seu ambiente em cada terminal. Em um workspace recém-clonado, instale as dependências do projeto e compile após carregar o ROS 2 base. Em alterações de código Python já instalado com symlink, reinicie o nó. Se alterou entradas do pacote, dependências ou arquivos instalados, recompile conforme necessário.</p>'+shell('os')+shell('setup')+shell('build'))+
   card('Terminal 1 · Mundo e robô','<p>Prefira o launch do projeto se ele inicia o mundo, o robô e a bridge. Para inspecionar só o SDF, use o comando Gazebo. O robô só aparece se estiver definido no mundo ou se você fizer o spawn pelo fluxo do projeto.</p>'+shell('launch')+shell('gazebo'))+
   card('Terminal 2 · Bridge e controle','<p>Se o launch já inicia a bridge e o nó Python, mantenha esta etapa para inspeção. Caso contrário, carregue a configuração de bridge do projeto e inicie o nó com <code>ros2 run &lt;pacote&gt; &lt;executável&gt;</code> ou pelo launch correspondente. O exemplo abaixo presume os mesmos nomes nos dois lados e mensagens Twist e LaserScan. Em outra aba, use <code>gz topic -l</code> para descobrir os nomes reais antes de adaptar a bridge.</p>'+shell('bridge'))+
   card('Terminal 3 · Inspeção','<p>Confira se o relógio da simulação avança, se o LiDAR publica e se existe assinante para o comando de velocidade. Ajuste nomes e namespaces conforme a lista de tópicos.</p>'+shell('topics')+shell('lidar')+shell('drive'))+
   card('Checklist da sessão',checklist())+'</div>';
 },
 comandos() {
   return head('Comandos salvos','Copie os comandos do roteiro e guarde os atalhos que funcionam no seu ambiente.')+'<div class="stack">'+card('Meus atalhos','<form id="custom"><label>Nome<input name="title" required maxlength="100"></label><label>Comando<textarea name="command" rows="2" required></textarea></label><button class="primary">Salvar comando</button></form>'+state.commands.map(c=>'<div class="terminal"><div class="row"><span>'+escapeHtml(c.title)+'</span><div class="tools"><button data-copy="custom:'+c.id+'">Copiar</button><button data-delete-command="'+c.id+'">Excluir</button></div></div><pre>'+escapeHtml(c.command)+'</pre></div>').join(''))+
   '<div class="grid">'+Object.entries(examples).map(([id,title])=>card(title,shell(id))).join('')+'</div></div>';
 },
 diagnostico(focus) {
   return head('Diagnóstico','Reproduza um sintoma por vez e salve as mensagens de tópico, a pose e um print antes de mudar o código.')+'<div class="stack">'+card('Condições do teste','<p>Execute os comandos de movimento apenas no simulador, em uma área livre e com o nó autônomo pausado. Confira antes se o tópico aceita <code>geometry_msgs/msg/Twist</code> e ajuste o nome se houver namespace. Os exemplos encerram cada teste enviando velocidade zero.</p>')+issues.map(([id,title,tag,steps,cmd])=>'<details class="card" '+(focus===id?'open':'')+'><summary>'+title+' <span class="kicker">· '+tag+'</span></summary><p>'+steps+'</p>'+shell(cmd)+(id==='lateral'?shell('rotate'):'')+'<button class="action" data-test="'+id+'">Registrar teste</button></details>').join('')+'</div>';
 },
 integracao() {
   return head('Integração 3D','Use o mesmo galpão como referência visual para a simulação e para a futura cena na Unity.')+
   '<div class="flow"><span>Blender</span><b>→</b><span>Malhas e colisões</span><b>→</b><span>warehouse_blender.sdf</span><b>→</b><span>Gazebo + ROS 2</span></div><div class="stack">'+
   card('Integração no Gazebo','<p>O launch padrão usa <code>warehouse_blender.sdf</code> com as malhas do AMR e do galpão SAFE4. A escala do galpão foi ajustada a 25%, o topo está aberto e as colisões das estruturas são aproximadas. O LiDAR simulado usa a ponte para publicar em <code>/scan</code>. A rota segue a odometria em <code>/odom</code>.</p><p>O grupo distribui o pacote ROS 2 separadamente.</p>')+
   card('Plano de integração com Unity','<ol><li>Importar uma versão visual do galpão, por exemplo em FBX, e posicionar o robô na mesma origem de referência da cena.</li><li>Manter a física no Gazebo e testar a Unity como visualizador. Prototipar a comunicação com ROS-TCP-Connector e um endpoint compatível com sua distribuição ROS 2.</li><li>Começar por pose de <code>/odom</code> ou <code>/tf</code>. Converter posição e orientação entre os eixos ROS e Unity, e comparar poses conhecidas na origem e após um deslocamento.</li><li>Adicionar LiDAR só após validar pose e latência. Registrar a versão de cada ferramenta e a divergência observada entre as cenas.</li></ol><a href="https://github.com/Unity-Technologies/ROS-TCP-Connector" target="_blank" rel="noopener">Referência do ROS-TCP-Connector ↗</a>')+'</div>';
 },
 ar() {
   return head('Realidade aumentada','Veja o AMR pela câmera do celular com o mesmo marcador usado em aula.')+
   card('Demonstração com o marcador Hiro','<ol><li>Abra o marcador em outra tela ou imprima a imagem.</li><li>No celular, abra a demonstração em uma aba do navegador e permita a câmera.</li><li>Aponte para o marcador inteiro, com a borda preta visível.</li></ol><div class="tools"><a class="primary action" href="ar.html" target="_blank" rel="noopener">Abrir câmera AR ↗</a><a class="action" href="https://raw.githubusercontent.com/AR-js-org/AR.js/master/data/images/hiro.png" target="_blank" rel="noopener">Abrir marcador Hiro ↗</a><a class="action" href="ar.html" download="RoboLab_AR.html">Baixar HTML</a></div><p>Também é possível colar o HTML no <code>index.html</code> de um projeto estático no StackBlitz. A validação da câmera e do marcador no celular está pendente.</p>');
 },
 paradigmas() {
   const items = [
    ['Python e orientação a objetos','Uma classe que herda de <code>Node</code> mantém assinatura, publicador e parâmetros. Separe a regra que analisa as distâncias da classe que lida com o ROS 2.'],
    ['ROS 2, nós e tópicos','Cada nó assume uma responsabilidade. O sensor publica em <code>/scan</code>, o controlador consome os dados e pode publicar em <code>/cmd_vel</code>. O tópico desacopla quem envia de quem recebe.'],
    ['Callbacks e eventos','O executor do ROS 2 chama a função registrada quando chega uma leitura. Um timer também dispara callbacks periódicos, por exemplo para checar se os dados do sensor ficaram antigos.'],
    ['Modularidade da simulação','Mundo SDF, sensor, bridge, controle Python e visual do Blender têm papéis distintos. Troque o mundo ou a interface visual mantendo o contrato de mensagens.'],
    ['Testes da regra e integração','Em teste unitário, passe uma lista de distâncias conhecidas à regra Python. Em teste de integração, posicione o robô diante de uma parede no Gazebo e compare <code>/scan</code>, <code>/cmd_vel</code> e a pose observada.'],
    ['Ubuntu e execução reproduzível','Registre distribuição ROS 2, pacote, launch e dependências. Um colega pode repetir o cenário e comparar os resultados com o diário.']
   ];
   return head('Paradigmas de Programação','Use exemplos do robô para demonstrar como o programa organiza estado, reage a eventos e permite testes.')+'<div class="grid">'+items.map(([t,p])=>card(t,'<p>'+p+'</p>')).join('')+'</div><div class="project-state">'+card('Exemplo didático · Callback de LiDAR','<p>Trecho para uso dentro de um nó <code>rclpy</code>, com os imports <code>LaserScan</code> e <code>qos_profile_sensor_data</code>. A função de decisão pode receber entradas fixas em um teste unitário.</p><div class="terminal"><pre>self.subscription = self.create_subscription(\n    LaserScan, "/scan", self.on_scan, qos_profile_sensor_data\n)\n\ndef on_scan(self, msg):\n    self.decisao = avaliar_distancias(msg.ranges)  # regra do projeto</pre></div>'+shell('test'))+'</div>';
 },
 diario() {
   const localIds = new Set(state.records.map(record => record.id));
   const rows=allRecords().filter(r=>(!filter||r.kind===filter)&&(!search||[r.title,r.notes,r.status].join(' ').toLocaleLowerCase().includes(search.toLocaleLowerCase())));
   return head('Diário do projeto','As evidências do projeto aparecem neste diário. Registros adicionados no navegador podem ser exportados em JSON.')+
   '<div class="stack">'+card('Registros','<div class="tools"><label>Buscar<input id="search" value="'+escapeHtml(search)+'" placeholder="Título, detalhes ou situação"></label><label>Tipo<select id="filter"><option value="">Todos</option>'+options(kinds,filter)+'</select></label><button id="export">Exportar JSON</button><button id="import">Importar JSON</button><input type="file" id="backup" accept=".json,application/json" hidden></div>')+
   (rows.length ? rows.map(r=>card(escapeHtml(r.title),'<div class="row"><span class="kicker">'+escapeHtml(r.kind)+' · '+escapeHtml(r.status)+'</span><small class="muted">'+new Date(r.date).toLocaleDateString('pt-BR')+'</small></div><p class="notes">'+escapeHtml(r.notes)+'</p>'+(r.photo?'<a href="'+escapeHtml(r.photo)+'" download="print-projeto"><img class="record-img" alt="Evidência do registro" src="'+escapeHtml(r.photo)+'"></a>':'')+(localIds.has(r.id)?'<div class="tools"><button data-edit="'+r.id+'">Editar</button><button data-delete="'+r.id+'">Excluir</button></div>':''))).join('') : card('Nenhum resultado','<p>Experimente outro filtro.</p>'))+'</div>';
 }
};
function render() {
  const [id, focus] = location.hash.slice(1).split('/');
  const [active,,title] = labels.find(([value])=>value===id) || labels[0];
  $('nav').innerHTML=labels.map(([key,icon,label])=>'<a href="#'+key+'" '+(key===active?'aria-current="page"':'')+'><span aria-hidden="true">'+icon+'</span>'+label+'</a>').join('');
  $('#crumb').textContent='Projeto / '+title;
  $('#view').innerHTML=pages[active](focus);
}
const form = $('#entry'), editor = $('#editor');
function edit(record={}, suggested='') {
  editId=record.id; form.reset();
  $('#form-title').textContent=editId?'Editar registro':'Novo registro';
  form.elements.kind.value=record.kind || (suggested?'Teste':kinds[0]);
  form.elements.title.value=record.title || suggested;
  form.elements.status.value=record.status || statuses[0];
  form.elements.notes.value=record.notes || (suggested?'Cenário e comando:\nResultado esperado:\nResultado observado:':'');
  $('#remove-label').hidden=!record.photo;
  editor.showModal();
}
$('#new').onclick=()=>edit();
$('#close').onclick=()=>editor.close();
const photoPattern=/^data:image\/(png|jpeg|webp);base64,[a-z0-9+/=]+$/i;
const makeId=()=>crypto.randomUUID();
form.onsubmit=async (event)=>{
  event.preventDefault();
  const submit=form.querySelector('button[type=submit], button.primary');
  submit.disabled=true;
  try {
    const fields=new FormData(form), title=fields.get('title').trim();
    if (!title) { toast('Digite um título.'); return; }
    const previous=state.records.find(r=>r.id===editId), file=form.elements.photo.files[0];
    let photo=fields.has('remove')?'':previous?.photo || '';
    if(file) {
      if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>2*1024*1024){toast('Escolha um PNG, JPEG ou WebP de até 2 MB.');return;}
      photo=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file);});
    }
    const record={id:editId||makeId(), kind:fields.get('kind'), status:fields.get('status'), title, notes:fields.get('notes'), photo, date:previous?.date||new Date().toISOString()};
    if(!save({records:previous?state.records.map(r=>r.id===editId?record:r):[record,...state.records]}))return;
    editor.close(); filter=''; search='';
    if(location.hash==='#diario')render();else location.hash='diario';
    toast('Registro salvo.');
  } catch { toast('Não foi possível ler o print.'); } finally {submit.disabled=false;}
};
$('#view').addEventListener('click',async (event)=>{
  const button=event.target.closest('button'); if(!button)return;
  const {copy,test,edit:entry,delete:id,deleteCommand}=button.dataset;
  if(copy){
    const command=copy.startsWith('custom:')?state.commands.find(c=>c.id===copy.slice(7))?.command:commands()[copy];
    try{await navigator.clipboard.writeText(command);toast('Comando copiado.');}catch{toast('Selecione o comando no bloco para copiar.');}
  }
  if(test)edit({},issues.find(row=>row[0]===test)[1]);
  if(entry)edit(state.records.find(r=>r.id===entry));
  if(id&&confirm('Excluir este registro?')&&save({records:state.records.filter(r=>r.id!==id)}))render();
  if(deleteCommand&&confirm('Excluir este comando?')&&save({commands:state.commands.filter(c=>c.id!==deleteCommand)}))render();
  if(button.id==='import')$('#backup').click();
  if(button.id==='export'){
    const url=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}));
    const a=document.createElement('a'); a.href=url; a.download='robolab-backup.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
});
function validBackup(data){
  const string=(v)=>typeof v==='string';
  const id=(v)=>string(v)&&/^[a-z0-9-]+$/i.test(v);
  return data && phases.includes(data.phase) && ['ws','distro','world','pkg','launch'].every(k=>string(data[k])) &&
    Array.isArray(data.checks)&&new Set(data.checks).size===data.checks.length&&data.checks.every(i=>Number.isInteger(i)&&i>=0&&i<checks.length) &&
    Array.isArray(data.commands)&&data.commands.every(c=>c&&id(c.id)&&string(c.title)&&string(c.command)) &&
    Array.isArray(data.records)&&data.records.every(r=>r&&id(r.id)&&kinds.includes(r.kind)&&statuses.includes(r.status)&&string(r.title)&&string(r.notes)&&string(r.date)&&Number.isFinite(Date.parse(r.date))&&(r.photo===''||(string(r.photo)&&photoPattern.test(r.photo))));
}
$('#view').addEventListener('change',async (event)=>{
  const element=event.target;
  if(element.dataset.check!==undefined){
    const i=Number(element.dataset.check);
    save({checks:element.checked?[...new Set([...state.checks,i])]:state.checks.filter(v=>v!==i)});
    const focus=element.dataset.check; render(); $("[data-check='"+focus+"']").focus();
  }
  if(element.id==='phase'&&!save({phase:element.value}))render();
  if(element.id==='filter'){filter=element.value;render();$('#filter').focus();}
  if(element.id==='backup'&&element.files[0]){
    try{
      const file=element.files[0]; if(file.size>6*1024*1024)throw Error();
      const data=JSON.parse(await file.text());
      if(!validBackup(data))throw Error();
      if(confirm('Substituir os dados atuais por este backup?')&&save(data)){filter='';search='';render();toast('Backup importado.');}
    } catch{toast('Escolha um backup válido exportado pelo RoboLab.');}
    element.value='';
  }
});
$('#view').addEventListener('input',event=>{
  if(event.target.id!=='search')return;
  const position=event.target.selectionStart;search=event.target.value;
  render();$('#search').focus();$('#search').setSelectionRange(position,position);
});
$('#view').addEventListener('submit',event=>{
  event.preventDefault();
  const f=new FormData(event.target);
  if(event.target.id==='config'){
    if(save(Object.fromEntries([...f].map(([k,v])=>[k,v.trim()])))){render();toast('Configuração salva.');}
  }
  if(event.target.id==='custom'){
    const title=f.get('title').trim(), command=f.get('command').trim();
    if(!title||!command){toast('Preencha nome e comando.');return;}
    if(save({commands:[...state.commands,{id:makeId(),title,command}]})){render();toast('Comando salvo.');}
  }
});
window.addEventListener('hashchange',()=>{render(); window.scrollTo(0,0);});
render();
