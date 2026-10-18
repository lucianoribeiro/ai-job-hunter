"""Interactive remuneration comparison with explicit illustrative assumptions."""
def render_advisor() -> str:
    return """
<section class="results" id="consultor" style="margin:22px 0">
<style>
.fc-head{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.fc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:18px 0}
.fc-field label{display:block}.fc-field input,.fc-field select{width:100%;font-size:16px}
.fc-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:18px}
.fc-card{border:1px solid #e1e7f0;background:#f8fafc;border-radius:14px;padding:17px;min-width:0}
.fc-card strong{display:block;font-size:clamp(19px,2vw,25px);color:#18345f;margin:9px 0;overflow-wrap:anywhere}
.fc-card small{color:#64748b;line-height:1.5}.fc-card-caption{color:#294e64;font-size:14px;font-weight:700;margin:8px 0 2px}.fc-card-name{color:#334155;font-weight:650}.fc-card.best{border-color:#0d9488;background:#f0fdfa}
.fc-note{font-size:12px;color:#64748b;line-height:1.6}
.fc-summary{padding:15px 17px;border-radius:12px;background:#f1f5f9;margin-top:15px;line-height:1.6}
</style>
<div class="fc-head"><div><h2 style="margin:0 0 5px">Consultor Financeiro · CLT × PJ × B2B</h2><p class="section-sub" style="margin:0">Informe seu salário CLT e calcule quanto precisaria faturar em outras modalidades. Só o salário é obrigatório.</p></div><span class="pill" style="color:#334155;border-color:#cbd5e1">Simulação ilustrativa</span></div>
<div class="fc-grid">
<div class="fc-field"><label for="fc-salary">Salário CLT bruto mensal (referência)</label><input id="fc-salary" type="text" inputmode="decimal" value="R$ 15.000,00" autocomplete="off"></div>
<div class="fc-field"><label for="fc-currency">Moeda de negociação</label><select id="fc-currency"><option value="BRL">Real (BRL)</option><option value="USD">Dólar (USD)</option></select></div>
<div class="fc-field"><label for="fc-contract">Tipo de proposta</label><select id="fc-contract"><option>CLT</option><option>PJ</option><option>B2B</option><option>Cooperativa</option></select></div>
<div class="fc-field"><label for="fc-fx">Cotação USD/BRL (PTAX ou manual)</label><input id="fc-fx" type="number" min="0.01" step=".0001" value="5.20"><button id="fc-refresh-fx" type="button">Atualizar PTAX</button><small id="fc-fx-status" role="status" aria-live="polite">Cotação inicial ilustrativa; aguardando consulta.</small></div>
</div>
<details><summary style="cursor:pointer;font-weight:700">Personalizar benefícios, impostos e premissas (opcional)</summary><div class="fc-grid">
<div class="fc-field"><label for="fc-benefits">Outros benefícios CLT mensais (R$)</label><input id="fc-benefits" type="text" inputmode="decimal" value="R$ 0,00"></div>
<div class="fc-field"><label for="fc-health">Plano de saúde (R$)</label><input id="fc-health" type="number" min="0" value="900"></div>
<div class="fc-field"><label for="fc-dental">Plano odontológico (R$)</label><input id="fc-dental" type="number" min="0" value="70"></div>
<div class="fc-field"><label for="fc-meal">Vale-refeição (R$)</label><input id="fc-meal" type="number" min="0" value="850"></div>
<div class="fc-field"><label for="fc-food">Vale-alimentação (R$)</label><input id="fc-food" type="number" min="0" value="0"></div>
<div class="fc-field"><label for="fc-insurance">Seguro de vida (R$)</label><input id="fc-insurance" type="number" min="0" value="60"></div>
<div class="fc-field"><label for="fc-pension">Previdência complementar (contribuição da empresa) (R$)</label><input id="fc-pension" type="number" min="0" value="0"></div>
<div class="fc-field"><label for="fc-health-discount">Desconto em folha: saúde (R$)</label><input id="fc-health-discount" type="number" min="0" value="0"></div>
<div class="fc-field"><label for="fc-dental-discount">Desconto em folha: odontológico (R$)</label><input id="fc-dental-discount" type="number" min="0" value="0"></div>
<div class="fc-field"><label for="fc-plr">PLR anual estimada (R$)</label><input id="fc-plr" type="number" min="0" value="0"></div>
<div class="fc-field"><label for="fc-margin">Margem desejada (%)</label><input id="fc-margin" type="number" min="0" value="20"></div>
<div class="fc-field"><label for="fc-tax">Imposto PJ/B2B estimado (%)</label><input id="fc-tax" type="number" min="0" max="100" value="12"></div>
<div class="fc-field"><label for="fc-cost">Custos mensais PJ/B2B (R$)</label><input id="fc-cost" type="text" inputmode="decimal" value="R$ 700,00"></div>
<div class="fc-field"><label for="fc-months">Meses faturados por ano</label><input id="fc-months" type="number" min="1" max="12" value="11"></div>
</div></details>
<div class="fc-grid">
<div class="fc-field"><label for="fc-pj-regime">Tributação PJ</label><select id="fc-pj-regime"><option value="simples">Simples Nacional (estimativa)</option><option value="presumido">Lucro Presumido (estimativa)</option></select></div>
<div class="fc-field"><label for="fc-activity">Atividade para Fator R</label><select id="fc-activity"><option value="subject">Serviços sujeitos ao Fator R (simulação)</option><option value="other">Outra atividade — consultar CNAE</option></select></div>
<div class="fc-field"><label for="fc-rbt">Receita bruta acumulada em 12 meses (R$)</label><input id="fc-rbt" type="number" min="0" step="1000" value="240000"></div>
<div class="fc-field"><label for="fc-payroll">Folha acumulada 12 meses incluindo encargos (R$)</label><input id="fc-payroll" type="number" min="0" step="1000" value="0"></div>
<div class="fc-field"><label for="fc-prolabore">Pró-labore mensal planejado (R$)</label><input id="fc-prolabore" type="number" min="0" step="100" value="0"></div>
<div class="fc-field"><label for="fc-personal-tax">Reserva para INSS/IRPF pessoal e encargos (%)</label><input id="fc-personal-tax" type="number" min="0" max="70" step=".5" value="10"></div>
<div class="fc-field"><label for="fc-fx-spread">Custo cambial / spread (%)</label><input id="fc-fx-spread" type="number" min="0" max="30" step=".1" value="2"></div>
<div class="fc-field"><label for="fc-iss">ISS presumido Lucro Presumido (%)</label><input id="fc-iss" type="number" min="2" max="5" step=".5" value="3"></div>
<div class="fc-field"><label for="fc-coop-fee">Taxa administrativa de cooperativa (%)</label><input id="fc-coop-fee" type="number" min="0" max="99" step=".1" value="15"></div>
<div class="fc-field"><label for="fc-coop-tax">Retenções / encargos cooperativa (%)</label><input id="fc-coop-tax" type="number" min="0" max="99" step=".1" value="11"></div>
</div>
<button type="button" id="fc-calculate" style="background:#357d6c;color:white;padding:12px 22px;border-radius:10px;font-weight:700;cursor:pointer">Calcular equivalência CLT → PJ / B2B / Cooperativa</button>
<div id="fc-results" role="status" aria-live="polite"></div>
<p class="fc-note">Estimativas para negociação, não cálculo tributário definitivo. A referência CLT considera salário bruto, 13º, férias, FGTS e benefícios; não calcula o líquido após IRRF/INSS. Para serviços sujeitos ao Fator R, a projeção usa as tabelas de Anexo III/V e folha/RBT12 informadas, sujeitas a validação com contador e regras vigentes. A referência de Lucro Presumido é simplificada (11,33% federais + ISS informado) e não apura adicional de IRPJ, retenções nem transição tributária. INSS/IRPF pessoal é apenas uma reserva editável, não cálculo de folha. Cooperativa exige verificar estatuto, contrato, encargos sobre a retirada e direitos reais. Verifique tudo com contador e assessoria jurídica.</p>
</section>
<script>
(function(){
const el=k=>document.getElementById('fc-'+k);
const fields=['salary','benefits','cost'];
const parse=v=>{let s=String(v).replace(/[^\\d,.-]/g,'');if(s.includes(','))s=s.replace(/\\./g,'').replace(',','.');else if((s.match(/\\./g)||[]).length>1)s=s.replace(/\\./g,'');return Math.max(0,Number(s)||0)};
const number=k=>Math.max(0,Number(el(k).value)||0);
const money=(v,c='BRL')=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:c}).format(v);
function format(k){const node=el(k),currency=k==='salary'?el('currency').value:'BRL';const raw=node.value.replace(/\\D/g,'');node.value=money((Number(raw)||0)/100,currency)}
function update(){
 const result=el('results');
 const currency=el('currency').value,contract=el('contract').value,fx=number('fx'),salary=parse(el('salary').value),brl=salary;
 if(!Number.isFinite(brl)||brl<=0){result.textContent='Informe seu salário CLT mensal para realizar o cálculo.';return;}
 const benefits=Math.max(0,parse(el('benefits').value)+number('health')+number('dental')+number('meal')+number('food')+number('insurance')+number('pension')-number('health-discount')-number('dental-discount'));
 const cost=parse(el('cost').value),months=Math.min(12,Math.max(1,number('months'))),margin=number('margin')/100;
 const regime=el('pj-regime').value;
 const rbt=number('rbt'),payroll=number('payroll')+number('prolabore')*12;
 const factor=rbt>0?payroll/rbt:null;
 const annex=factor!==null&&factor>=.28?'III':'V';
 const brackets=annex==='III'?[[180000,.06,0],[360000,.112,9360],[720000,.135,17640],[1800000,.16,35640],[3600000,.21,125640],[4800000,.33,648000]]:[[180000,.155,0],[360000,.18,4500],[720000,.195,9900],[1800000,.205,17100],[3600000,.23,62100],[4800000,.305,540000]];
 const bracket=brackets.find(b=>rbt<=b[0]);
 const effectiveSimples=bracket&&rbt>0?(rbt*bracket[1]-bracket[2])/rbt:null;
 const effectiveTax=regime==='simples'?(el('activity').value==='subject'&&effectiveSimples!==null?effectiveSimples:Math.min(.99,number('tax')/100)):(.1133+number('iss')/100);
 const personalReserve=Math.min(.7,number('personal-tax')/100);
 const personalCost=number('prolabore')*personalReserve;
 const coopFee=Math.min(0.99,number('coop-fee')/100),coopTax=Math.min(0.99,number('coop-tax')/100);
 // Approximate economic gross compensation; not CLT net take-home pay.
 const clt=brl*(13+1/3)*1.08+benefits*12+number('plr');
 const annualTarget=clt*(1+margin);
 function required(rate,monthlyCost){
   const retained=1-rate;
   return retained>0?(annualTarget+monthlyCost*months)/(months*retained):null;
 }
 const pj=required(effectiveTax,cost+personalCost),coop=required(coopFee+coopTax,0);
 const spread=Math.min(.3,number('fx-spread')/100),international=required(effectiveTax+(1-effectiveTax)*spread,cost+personalCost);
 const scenarios=[
  {name:'PJ · '+(regime==='simples'?'Simples Nacional':'Lucro Presumido'),amount:pj,rate:effectiveTax,detail:'Valor de nota fiscal mensal para prestar serviços como empresa no Brasil. Inclui impostos e custos estimados; não é salário líquido.',heading:'Quanto pedir como PJ nacional'},
  {name:'B2B internacional',amount:international,rate:effectiveTax,detail:'Valor mensal para negociar com empresa estrangeira, geralmente em USD. Inclui spread estimado; não representa o líquido recebido.',heading:'Quanto pedir em B2B internacional'},
  {name:'Cooperativa',amount:coop,rate:coopFee+coopTax,detail:'Valor mensal de contrato por intermédio de cooperativa, antes de taxas e encargos. Confira as regras de repasse e o estatuto.',heading:'Quanto pedir via cooperativa'},
 ];
 const factorNote=regime==='simples'&&el('activity').value==='subject'?
  (factor===null?'RBT12 não informada; alíquota manual utilizada.':'Fator R estimado: '+(factor*100).toFixed(1)+'%; Anexo '+annex+' considerado. Alíquota efetiva aproximada: '+(effectiveTax*100).toFixed(2)+'%.'):
  'Atividade/regime não validado; aplicada premissa tributária configurável.';
 const cards=scenarios.map(x=>{
  const isB2B=x.name==='B2B internacional',showUsd=isB2B||currency==='USD';
  const negotiated=x.amount===null?'Inviável com as taxas atuais':money(showUsd?x.amount/Math.max(fx,.01):x.amount,showUsd?'USD':'BRL')+'/mês';
  const converted=x.amount===null?'':'<br>Equivalente em '+(showUsd?'BRL: '+money(x.amount):'USD: '+money(x.amount/Math.max(fx,.01),'USD'));
  return '<article class="fc-card"><span class="fc-card-name">'+x.name+'</span><p class="fc-card-caption">'+x.heading+'</p><strong>'+negotiated+'</strong><small><b>Faturamento/valor bruto mensal sugerido — não é salário líquido.</b><br>Alíquota/encargos percentuais estimados: '+(x.rate*100).toFixed(1)+'%<br>'+x.detail+converted+'</small></article>';
 }).join('');
 result.innerHTML='<div class="fc-summary"><strong>Sua referência: CLT bruto + benefícios anuais</strong><div>'+money(clt)+' · '+money(clt/12)+'/mês</div><small>Inclui provisões de 13º, férias + 1/3, FGTS estimado, benefícios e PLR. Margem desejada: '+(margin*100).toFixed(0)+'%.</small></div><div class="fc-cards">'+cards+'</div><div class="fc-summary"><strong>Como interpretar</strong><p>Os cenários tributários dependem de CNAE, município e enquadramento confirmado. Reserva pessoal sobre pró-labore informada separadamente. Esses valores representam faturamento mensal-alvo durante '+months+' meses faturados, não salário líquido nem imposto apurado. Compare também segurança contratual, férias não remuneradas, seguro, riscos de rescisão, tributação e encargos pessoais.</p></div>';
}

fields.forEach(k=>{el(k).addEventListener('blur',()=>format(k));el(k).addEventListener('focus',()=>el(k).select())});
el('contract').addEventListener('change',()=>{el('currency').value=el('contract').value==='B2B'?'USD':'BRL';});
async function loadPtax(){
 const status=el('fx-status');status.textContent='Consultando PTAX do Banco Central...';
 const today=new Date();
 for(let i=0;i<9;i++){
  const day=new Date(today);day.setDate(today.getDate()-i);
  const d=String(day.getDate()).padStart(2,'0'),m=String(day.getMonth()+1).padStart(2,'0'),y=day.getFullYear();
  const endpoint="https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='"+m+'-'+d+'-'+y+"'&$format=json";
  try{
   const response=await fetch(endpoint,{signal:AbortSignal.timeout(4500)});
   if(!response.ok)continue;
   const data=await response.json(),values=Array.isArray(data.value)?data.value:[];
   const quote=values.find(x=>Number(x.cotacaoVenda)>0);
   if(!quote)continue;
   el('fx').value=Number(quote.cotacaoVenda).toFixed(4);
   status.textContent='PTAX venda BCB de '+d+'/'+m+'/'+y+' (referência; não é cotação comercial).';
   return;
  }catch(error){if(i===8)break;}
 }
 status.textContent='PTAX indisponível ou bloqueada pelo navegador. Use a cotação manual; valor atual não foi validado.';
}
el('refresh-fx').addEventListener('click',loadPtax);
el('fx').addEventListener('input',()=>el('fx-status').textContent='Cotação manual — confirme o valor aplicado.');
loadPtax();
el('calculate').addEventListener('click',update);

})();
</script>
""";
