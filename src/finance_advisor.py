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
<div class="fc-head"><div><h2 style="margin:0 0 5px">Consultor Financeiro · CLT × PJ × B2B</h2><p class="section-sub" style="margin:0">Digite o valor e compare cenários automaticamente.</p></div><span class="pill" style="color:#334155;border-color:#cbd5e1">Simulação ilustrativa</span></div>
<div class="fc-grid">
<div class="fc-field"><label for="fc-salary">Salário / proposta mensal</label><input id="fc-salary" type="text" inputmode="decimal" value="R$ 15.000,00" autocomplete="off"></div>
<div class="fc-field"><label for="fc-currency">Moeda da proposta</label><select id="fc-currency"><option value="BRL">Real (BRL)</option><option value="USD">Dólar (USD)</option></select></div>
<div class="fc-field"><label for="fc-contract">Tipo de proposta</label><select id="fc-contract"><option>CLT</option><option>PJ</option><option>B2B</option></select></div>
<div class="fc-field"><label for="fc-fx">Cotação USD/BRL (premissa)</label><input id="fc-fx" type="number" min="0.01" step=".01" value="5.20"></div>
</div>
<details><summary style="cursor:pointer;font-weight:700">Personalizar premissas</summary><div class="fc-grid">
<div class="fc-field"><label for="fc-benefits">Benefícios CLT mensais (R$)</label><input id="fc-benefits" type="text" inputmode="decimal" value="R$ 1.500,00"></div>
<div class="fc-field"><label for="fc-tax">Imposto PJ/B2B estimado (%)</label><input id="fc-tax" type="number" min="0" max="100" value="12"></div>
<div class="fc-field"><label for="fc-cost">Custos mensais PJ/B2B (R$)</label><input id="fc-cost" type="text" inputmode="decimal" value="R$ 700,00"></div>
<div class="fc-field"><label for="fc-months">Meses faturados por ano</label><input id="fc-months" type="number" min="1" max="12" value="11"></div>
</div></details>
<div id="fc-results" role="status" aria-live="polite"></div>
<p class="fc-note">Estimativas de comparação, não valores líquidos fiscais. CLT inclui salário bruto, 13º, adicional de férias e benefícios; não desconta IRRF/INSS nem incorpora FGTS. PJ/B2B descontam apenas alíquota e custos informados, sem apuração de DAS, fator R, pró-labore, INSS, IRPF, câmbio efetivo, retenções ou tributação de exportação. A comparação não considera riscos contratuais. Consulte contador antes de decidir.</p>
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
const currency=el('currency').value,contract=el('contract').value,fx=number('fx'),salary=parse(el('salary').value),brl=salary*(currency==='USD'?fx:1);
const benefits=parse(el('benefits').value),tax=Math.min(100,number('tax'))/100,cost=parse(el('cost').value),months=Math.min(12,Math.max(1,number('months')));
const clt=brl*(13+1/3)+benefits*12;
const net=(brl*(1-tax)-cost)*months;
const names=['CLT','PJ','B2B'];
const amounts={CLT:clt,PJ:net,B2B:net};
const cards=names.map(name=>'<article class="fc-card '+(name===contract?'best':'')+'"><span>'+name+(name===contract?' · Sua proposta':' · Equivalência')+'</span><strong>'+money(amounts[name])+'</strong><small>Projeção anual '+(name==='CLT'?'bruta + benefícios':'após imposto e custos estimados')+'<br>Média mensal: '+money(amounts[name]/12)+'</small></article>').join('');
const delta=net-clt, difference=money(Math.abs(delta));
const note=contract==='CLT'?'Sua proposta CLT tem projeção anual bruta de '+money(clt)+'. Compare com a estimativa PJ/B2B de '+money(net)+'.':'Sua proposta '+contract+' tem projeção anual estimada de '+money(net)+'. A referência CLT bruta com benefícios seria '+money(clt)+'.';
el('fc-results').innerHTML='<div class="fc-cards">'+cards+'</div><div class="fc-summary"><strong>Leitura da proposta</strong><div>'+note+'</div><small>Diferença ilustrativa PJ/B2B versus CLT: '+(delta>=0?'+':'−')+difference+'. Não é uma recomendação definitiva: bases fiscais diferentes exigem análise tributária e benefícios individualizados.</small></div>';
}
fields.forEach(k=>{el(k).addEventListener('input',()=>{format(k);update()});el(k).addEventListener('focus',()=>el(k).select())});
['fx','tax','months','contract'].forEach(k=>el(k).addEventListener('input',update));
el('currency').addEventListener('change',()=>{const amount=parse(el('salary').value);el('salary').value=money(amount,el('currency').value);update()});
update();
})();
</script>
""";
