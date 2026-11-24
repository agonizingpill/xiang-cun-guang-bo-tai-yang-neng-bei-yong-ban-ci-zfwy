        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "从两日用量核算备用",
  "module": "备用分钟核算",
  "caption": "备用分钟核算",
  "detail": "以 24 小时周期的 Fourier 基拟合，并保留末六小时验证。",
  "path": "/reserves",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "airslot",
      "label": "节目时段"
    },
    {
      "name": "plan_wh",
      "label": "计划备用 Wh"
    },
    {
      "name": "fallback",
      "label": "备用源优先级"
    },
    {
      "name": "mae",
      "label": "时间验证MAE Wh"
    },
    {
      "name": "token",
      "label": "计算号"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "forecast_wh",
      "label": "计算周期用量与备量",
      "path": "/reserves/forecast-wh",
      "fields": [
        {
          "name": "airslot",
          "label": "节目编号",
          "kind": "text",
          "initial": "AIR-17"
        },
        {
          "name": "meter",
          "label": "电表",
          "kind": "text",
          "initial": "BAT-04"
        },
        {
          "name": "clear",
          "label": "计划日晴天",
          "kind": "bool",
          "initial": true
        }
      ],
      "help": "使用整点记录和次日晴天状态，返回备用建议。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "save_reserve",
      "label": "记录备用量评估",
      "path": "/reserves/save-reserve",
      "fields": [
        {
          "name": "code",
          "label": "备用评估单",
          "kind": "text",
          "initial": "RV-24"
        },
        {
          "name": "token",
          "label": "计算号",
          "kind": "token",
          "initial": ""
        }
      ],
      "help": "按调班时对应的许可情况留下备用评估。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "reserves";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
