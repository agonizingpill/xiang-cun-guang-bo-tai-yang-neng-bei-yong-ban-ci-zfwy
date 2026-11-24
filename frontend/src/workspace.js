import {request} from './api.js';
import {actionForm} from './controls.js';
import {el} from './dom.js';
import {dataView, status, titleBlock} from './widgets.js';

export function workspace(root, role, page) {
  const panel = el('section', {class:'ledger', 'aria-label':page.caption});
  const refresh = async () => {
    try {
      const rows = await request(page.path);
      panel.replaceChildren(el('h2',{},page.caption),dataView(rows, page.columns,page.view));
    } catch (error) { panel.replaceChildren(status(error.message,'error')); }
  };
  const actions = page.actions.filter(x => x.roles.includes(role));
  root.replaceChildren(titleBlock(page.module, page.title, page.detail),
    el('div',{class:'work '+page.layout},panel,
      actions.length ? el('section',{class:'actions'},actions.map(x => actionForm(x, refresh))) : null));
  return refresh();
}
