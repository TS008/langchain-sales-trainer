import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st

class ReportManager:
    """报告管理器，负责保存、加载和管理复盘报告"""
    
    def __init__(self, reports_dir: str = "data/reports"):
        self.reports_dir = reports_dir
        self.ensure_reports_directory()
    
    def ensure_reports_directory(self):
        """确保报告目录存在"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def save_report(self, report_content: str, persona: str, conversation_history: List[Dict]) -> str:
        """
        保存复盘报告
        返回报告ID
        """
        timestamp = datetime.now()
        report_id = timestamp.strftime("%Y%m%d_%H%M%S")
        
        report_data = {
            "id": report_id,
            "timestamp": timestamp.isoformat(),
            "persona": persona,
            "report_content": report_content,
            "conversation_history": conversation_history,
            "conversation_length": len(conversation_history)
        }
        
        # 保存为JSON文件
        filename = f"report_{report_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return report_id
    
    def load_report(self, report_id: str) -> Optional[Dict]:
        """加载指定的报告"""
        filename = f"report_{report_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载报告失败: {e}")
            return None
    
    def get_all_reports(self) -> List[Dict]:
        """获取所有报告的概要信息"""
        reports = []
        
        if not os.path.exists(self.reports_dir):
            return reports
        
        for filename in os.listdir(self.reports_dir):
            if filename.startswith("report_") and filename.endswith(".json"):
                filepath = os.path.join(self.reports_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                        # 只保留概要信息
                        summary = {
                            "id": report_data["id"],
                            "timestamp": report_data["timestamp"],
                            "persona": report_data["persona"],
                            "conversation_length": report_data.get("conversation_length", 0),
                            "date_formatted": datetime.fromisoformat(report_data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        reports.append(summary)
                except Exception as e:
                    st.warning(f"读取报告文件 {filename} 时出错: {e}")
        
        # 按时间戳倒序排列
        reports.sort(key=lambda x: x["timestamp"], reverse=True)
        return reports
    
    def delete_report(self, report_id: str) -> bool:
        """删除报告"""
        filename = f"report_{report_id}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            st.error(f"删除报告失败: {e}")
            return False
    
    def export_report_to_markdown(self, report_data: Dict) -> str:
        """将报告导出为Markdown格式"""
        md_content = f"""# 销售模拟复盘报告

## 基本信息
- **报告ID**: {report_data['id']}
- **生成时间**: {datetime.fromisoformat(report_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
- **客户类型**: {report_data['persona']}
- **对话轮数**: {report_data.get('conversation_length', 0)}

## 评估报告
{report_data['report_content']}

## 完整对话记录
"""
        
        for i, message in enumerate(report_data['conversation_history'], 1):
            role = "销售" if message['role'] == 'salesperson' else "客户"
            md_content += f"\n**{i}. {role}**: {message['content']}\n"
        
        return md_content
    
    def export_reports_to_excel(self, report_ids: List[str]) -> bytes:
        """将多个报告导出为Excel文件"""
        reports_data = []
        
        for report_id in report_ids:
            report_data = self.load_report(report_id)
            if report_data:
                # 提取报告中的评分信息（这里需要解析报告内容）
                summary_data = {
                    "报告ID": report_data['id'],
                    "生成时间": datetime.fromisoformat(report_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    "客户类型": report_data['persona'],
                    "对话轮数": report_data.get('conversation_length', 0),
                    "完整报告": report_data['report_content']
                }
                reports_data.append(summary_data)
        
        # 创建Excel文件
        df = pd.DataFrame(reports_data)
        
        # 使用BytesIO来在内存中创建Excel文件
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='复盘报告', index=False)
        
        return output.getvalue()

# 全局报告管理器实例
report_manager = ReportManager() 