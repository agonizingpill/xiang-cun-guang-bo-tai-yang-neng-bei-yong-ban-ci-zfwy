        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "班记抄表与见证",
  "module": "蓄电班记与测量",
  "caption": "蓄电班记与测量",
  "detail": "抄表按电表编号和两日内小时保持唯一，未经确认的数据不进入周期拟合。",
  "path": "/battery_logs",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "meter",
      "label": "电表编号"
    },
    {
      "name": "hour",
      "label": "两日内整点"
    },
    {
      "name": "load_wh",
      "label": "用量 Wh"
    },
    {
      "name": "clear",
      "label": "天空晴"
    },
    {
      "name": "verified",
      "label": "抄表审核"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "log_charge",
      "label": "登记整点电量",
      "path": "/battery_logs/log-charge",
      "fields": [
        {
          "name": "code",
          "label": "抄表号",
          "kind": "text",
          "initial": "WH-RECHECK"
        },
        {
          "name": "meter",
          "label": "电表",
          "kind": "text",
          "initial": "BAT-11"
        },
        {
          "name": "hour",
          "label": "两日内小时",
          "kind": "int",
          "initial": 7
        },
        {
          "name": "load_wh",
          "label": "整点用量 Wh",
          "kind": "float",
          "initial": 88.4
        },
        {
          "name": "clear",
          "label": "晴天",
          "kind": "bool",
          "initial": true
        }
      ],
      "help": "抄表数据保留班记来源。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "approve_meter",
      "label": "核对班记读数",
      "path": "/battery_logs/approve-meter",
      "fields": [
        {
          "name": "record",
          "label": "抄表号",
          "kind": "text",
          "initial": "WH-RECHECK"
        }
      ],
      "help": "将纸本班记单据与读数签认。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "battery_logs";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
