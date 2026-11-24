        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "离线版权与节目时刻",
  "module": "节目时段表",
  "caption": "节目时段表",
  "detail": "节目可以临时登记为离线，班组在签发时重新核对版权状态。",
  "path": "/airslots",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "title",
      "label": "节目"
    },
    {
      "name": "hour",
      "label": "起播小时"
    },
    {
      "name": "license",
      "label": "节目源许可"
    },
    {
      "name": "offline",
      "label": "离线时段"
    }
  ],
  "layout": "flip",
  "view": "stack",
  "actions": [
    {
      "name": "mark_offline",
      "label": "登记版权离线窗口",
      "path": "/airslots/mark-offline",
      "fields": [
        {
          "name": "airslot",
          "label": "节目编号",
          "kind": "text",
          "initial": "AIR-08"
        },
        {
          "name": "offline",
          "label": "版权离线",
          "kind": "bool",
          "initial": false
        }
      ],
      "help": "复核员依据节目源凭单登记。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "airslots";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
