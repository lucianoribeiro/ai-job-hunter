"""Regression for Recruiter Monitor filter DOM behavior and card visibility."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from src.unified_jobs_dashboard import render


class RecruiterFilterBehaviorTests(unittest.TestCase):
    def test_hidden_cards_override_flex_css(self):
        page = render({"jobs": []}, [])
        self.assertIn(".recruiter-card[hidden]{display:none!important}", page)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_qa_selection_hides_manufacturing_and_combines_filters(self):
        page = render({"jobs": []}, [])
        begin = page.index("const recruiterArea=document.getElementById('recruiter-area')")
        end = page.index("document.querySelector('.ai-tab", begin)
        script = page[begin:end]
        harness = """
const ids=['recruiter-area','recruiter-mode','recruiter-usd','recruiter-origin','recruiter-contract'];
const elements=Object.fromEntries(ids.map(id=>[id,{value:'',listeners:{},addEventListener(event,fn){this.listeners[event]=fn}}]));
elements['recruiter-count']={textContent:''};
const cards=[
 {dataset:{area:'QA',mode:'Remoto confirmado',usd:'yes',origin:'Empresa',contract:'B2B'},hidden:false},
 {dataset:{area:'Manufatura',mode:'Não informada',usd:'no',origin:'Não verificada',contract:'CLT'},hidden:false},
 {dataset:{area:'QA',mode:'Não informada',usd:'no',origin:'Não verificada',contract:'CLT'},hidden:false}
];
global.document={
 getElementById:id=>elements[id]||null,
 querySelectorAll:selector=>selector==='.recruiter-card'?cards:[]
};
""" + script + """
const change=(id,value)=>{elements[id].value=value;elements[id].listeners.change();};
change('recruiter-area','QA');
if(cards[1].hidden!==true||cards[0].hidden||cards[2].hidden)throw Error('Area QA did not hide manufacturing');
if(elements['recruiter-count'].textContent!=='2')throw Error('QA count incorrect');
change('recruiter-usd','yes');
if(cards[2].hidden!==true||cards[0].hidden!==false)throw Error('USD combination broken');
change('recruiter-contract','CLT');
if(cards.some(x=>!x.hidden))throw Error('Combined filters should show none');
if(elements['recruiter-count'].textContent!=='0')throw Error('Zero count incorrect');
"""
        completed = subprocess.run(["node", "-e", harness], capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
