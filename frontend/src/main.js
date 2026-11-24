import {login} from './login.js';
import {el} from './dom.js';
import {ROLES, session, setSession} from './store.js';
import {info, pages} from './pages/index.js';

const root = document.getElementById('app');
function render() {
  if (!session()) {
    login(root, info, render);
    return;
  }
  const slug = location.hash.slice(1);
  const current = pages.find(page => page.key === slug) || pages[0];
  const workspace = el('main',{id:'workspace'});
  root.replaceChildren(el('header',{class:'top'},el('div',{class:'brand'},info.title),
    el('span',{},ROLES[session().role]),el('button',{class:'quiet',onclick:() => {
      setSession(null); render();
    }},'退出')),
  el('div',{class:'shell'},el('nav',{'aria-label':'业务模块'},pages.map(page =>
    el('a',{href:'#'+page.key,'aria-current':page === current ? 'page' : undefined},page.title))),workspace));
  current.render(workspace,session().role);
}
window.addEventListener('hashchange',render);
render();
