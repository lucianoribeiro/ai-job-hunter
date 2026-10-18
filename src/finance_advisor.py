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
.fc-card small{color:#64748b;line-height:1.5}.fc-card.best{border-color:#0d9488;background:#f0fdfa}
.fc-note{font-size:12px;color:#64748b;line-height:1.6}
.fc-summary{padding:15px 17px;border-radius:12px;background:#f1f5f9;margin-top:15px;line-height:1.6}
</style>
<div class="fc-head"><div><h2 style="margin:0 0 5px">Consultor Financeiro · CLT × PJ × B2B</h2><p class="section-sub" style="margin:0">Informe seu salário CLT e calcule quanto precisaria faturar em outras modalidades. Só o salário é obrigatório.</p></div><span class="pill" style="color:#334155;border-color:#cbd5e1">Simulação ilustrativa</span></div>
<div class="fc-grid">
<div class="fc-field"><label for="fc-salary">Salário CLT bruto mensal (referência)</label><input id="fc-salary" type="text" inputmode="decimal" value="R$ 15.000,00" autocomplete="off"></div>
<div class="fc-field"><label for="fc-currency">Moeda da proposta</label><select id="fc-currency"><option value="BRL">Real (BRL)</option><option value="USD">Dólar (USD)</option></select></div>
<div class="fc-field"><label for="fc-contract">Tipo de proposta</label><select id="fc-contract"><option>CLT</option><option>PJ</option><option>B2B</option></select></div>
<div class="fc-field"><label for="fc-fx">Cotação USD/BRL (premissa)</label><input id="fc-fx" type="number" min="0.01" step=".01" value="5.20"></div>
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
<div class="fc-field"><label for="fc-coop-fee">Taxa administrativa de cooperativa (%)</label><input id="fc-coop-fee" type="number" min="0" max="99" step=".1" value="15"></div>
<div class="fc-field"><label for="fc-coop-tax">Retenções / encargos cooperativa (%)</label><input id="fc-coop-tax" type="number" min="0" max="99" step=".1" value="11"></div>
</div>
<button type="button" id="fc-calculate" style="background:#357d6c;color:white;padding:12px 22px;border-radius:10px;font-weight:700;cursor:pointer">Calcular equivalência CLT → PJ / B2B / Cooperativa</button>
<div id="fc-results" role="status" aria-live="polite"></div>
<p class="fc-note">Estimativas para negociação, não cálculo tributário definitivo. A referência CLT considera salário bruto, 13º, férias, FGTS e benefícios; não calcula o líquido após IRRF/INSS. As alíquotas PJ são cenários configuráveis, não substituem enquadramento CNAE, anexos do Simples, Fator R, ISS municipal, pró-labore, INSS/IRPF, contabilidade, retenções e regime de exportação. Cooperativa exige verificar estatuto, contrato, encargos sobre a retirada e direitos reais. Verifique tudo com contador e assessoria jurídica.</p>
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
 const currency=el('currency').value,fx=number('fx'),salary=parse(el('salary').value),brl=salary*(currency==='USD'?fx:1);
 if(!Number.isFinite(brl)||brl<=0){result.textContent='Informe seu salário CLT mensal para realizar o cálculo.';return;}
 const benefits=Math.max(0,parse(el('benefits').value)+number('health')+number('dental')+number('meal')+number('food')+number('insurance')+number('pension')-number('health-discount')-number('dental-discount'));
 const cost=parse(el('cost').value),months=Math.min(12,Math.max(1,number('months'))),margin=number('margin')/100;
 const regime=el('pj-regime').value;
 const effectiveTax=regime==='simples'?Math.min(0.99,number('tax')/100):0.165;
 const coopFee=Math.min(0.99,number('coop-fee')/100),coopTax=Math.min(0.99,number('coop-tax')/100);
 // Approximate economic gross compensation; not CLT net take-home pay.
 const clt=brl*(13+1/3)*1.08+benefits*12+number('plr');
 const annualTarget=clt*(1+margin);
 function required(rate,monthlyCost){
   const retained=1-rate;
   return retained>0?(annualTarget+monthlyCost*months)/(months*retained):null;
 }
 const pj=required(effectiveTax,cost),coop=required(coopFee+coopTax,0);
 const scenarios=[
  {name:'PJ · '+(regime==='simples'?'Simples Nacional':'Lucro Presumido'),amount:pj,rate:effectiveTax,detail:'Tributos efetivos assumidos + custos administrativos'},
  {name:'B2B internacional',amount:pj,rate:effectiveTax,detail:'Mesma premissa PJ, antes de câmbio efetivo, IOF e regras de exportação'},
  {name:'Cooperativa',amount:coop,rate:coopFee+coopTax,detail:'Taxa administrativa e encargos editáveis; sem custos PJ'},
 ];
 const cards=scenarios.map(x=>'<article class="fc-card"><span>'+x.name+'</span><strong>'+(x.amount===null?'Inviável com as taxas atuais':money(x.amount)+'/mês')+'</strong><small>Retenções assumidas: '+(x.rate*100).toFixed(1)+'%<br>'+x.detail+'<br>'+(x.amount!==null?'Equivalente USD pela cotação informada: '+money(x.amount/Math.max(fx,.01),'USD'):'')+'</small></article>').join('');
 result.innerHTML='<div class="fc-summary"><strong>Referência CLT anual (valor econômico bruto)</strong><div>'+money(clt)+' · '+money(clt/12)+'/mês</div><small>Inclui provisões de 13º, férias + 1/3, FGTS estimado, benefícios e PLR. Margem desejada: '+(margin*100).toFixed(0)+'%.</small></div><div class="fc-cards">'+cards+'</div><div class="fc-summary"><strong>Como interpretar</strong><p>Esses valores representam faturamento mensal-alvo durante '+months+' meses faturados, não salário líquido nem imposto apurado. Compare também segurança contratual, férias não remuneradas, seguro, riscos de rescisão, tributação e encargos pessoais.</p></div>';
}

fields.forEach(k=>{el(k).addEventListener('blur',()=>format(k));el(k).addEventListener('focus',()=>el(k).select())});
el('currency').addEventListener('change',()=>{el('salary').value=money(parse(el('salary').value),el('currency').value)});
el('calculate').addEventListener('click',update);

})();
</script>
""";
