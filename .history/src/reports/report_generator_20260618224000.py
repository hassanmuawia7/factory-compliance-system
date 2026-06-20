"""
Reporting Module - Generate compliance reports in multiple formats
Supports CSV, JSON, and Summary reports from the database.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import json
from datetime import datetime
from src.database.database_service import DatabaseService
from src.severity.event_factory import SeverityClassifier


class ReportGenerator:
    """Generate compliance reports in various formats."""
    
    @staticmethod
    def generate_csv_report(output_path: str = None) -> str:
        """
        Generate CSV report of all violations.
        
        Args:
            output_path: Output file path. If None, generates default filename
            
        Returns:
            str: Path to generated file
        """
        df = DatabaseService.get_all_violations()
        
        if output_path is None:
            output_path = f"outputs/reports/compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"✅ CSV Report generated: {output_path}")
        return output_path
    
    @staticmethod
    def generate_json_report(output_path: str = None) -> str:
        """
        Generate JSON report of all violations.
        
        Args:
            output_path: Output file path. If None, generates default filename
            
        Returns:
            str: Path to generated file
        """
        df = DatabaseService.get_all_violations()
        
        if output_path is None:
            output_path = f"outputs/reports/compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert dataframe to JSON with proper formatting
        records = df.to_dict(orient='records')
        with open(output_path, 'w', encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        
        print(f"✅ JSON Report generated: {output_path}")
        return output_path
    
    @staticmethod
    def generate_summary_report(output_path: str = None) -> str:
        """
        Generate comprehensive summary report.
        
        Args:
            output_path: Output file path. If None, generates default filename
            
        Returns:
            str: Path to generated file
        """
        if output_path is None:
            output_path = f"outputs/compliance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get statistics
        stats = DatabaseService.get_statistics()
        df = DatabaseService.get_all_violations()
        
        # Generate report content
        report = f"""
================================================================================
                    FACTORY COMPLIANCE MONITORING REPORT
================================================================================

Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
EXECUTIVE SUMMARY
================================================================================

Total Events Logged:        {stats['total_violations']}
Compliance Score:           {stats['compliance_score']:.1f}%
Database Status:            {'Connected' if stats['database_connected'] else 'ERROR'}

================================================================================
VIOLATION BREAKDOWN
================================================================================

CRITICAL Violations:        {stats['critical_count']}
HIGH Violations:            {stats['high_count']}
MEDIUM Violations:          {stats['medium_count']}
LOW Violations:             {stats['low_count']}

Violation Impact Score:
  - Each CRITICAL event: -5 points
  - Each HIGH event:     -2 points
  - Each MEDIUM event:   -0.5 points

================================================================================
VIOLATIONS BY BEHAVIOR TYPE
================================================================================
"""
        
        if not df.empty:
            behavior_dist = df['behavior_class'].value_counts()
            for behavior, count in behavior_dist.items():
                report += f"\n{behavior.upper().replace('_', ' ')}: {count} events"
        
        report += f"""

================================================================================
RECENT CRITICAL & HIGH VIOLATIONS (Top 10)
================================================================================
"""
        
        if not df.empty:
            recent = df[df['severity'].isin(['CRITICAL', 'HIGH'])].head(10)
            for idx, row in recent.iterrows():
                report += f"""
Event ID:       {row['event_id']}
Timestamp:      {row['timestamp']}
Severity:       {row['severity']}
Behavior:       {row['behavior_class']}
Description:    {row['description']}
Policy:         {row['policy_rule_ref']}
Action:         {row['escalation_action']}
"""
        
        report += """
================================================================================
RECOMMENDATIONS
================================================================================

"""
        
        # Generate recommendations based on statistics
        if stats['critical_count'] > 0:
            report += f"""
⚠️  URGENT: {stats['critical_count']} critical violations require immediate action.
   - Review all CRITICAL severity events
   - Implement corrective measures
   - Increase monitoring frequency

"""
        
        if stats['high_count'] > 5:
            report += f"""
⚠️  ATTENTION: {stats['high_count']} high-severity violations detected.
   - Investigate root causes
   - Update safety protocols
   - Conduct training sessions

"""
        
        if stats['compliance_score'] < 80:
            report += f"""
⚠️  WARNING: Compliance score below 80%.
   - Comprehensive safety audit recommended
   - Review detection system calibration
   - Update compliance policies

"""
        else:
            report += f"""
✅ GOOD: Compliance score is {stats['compliance_score']:.1f}%.
   - Continue current safety protocols
   - Monitor trending violations
   - Regular system maintenance

"""
        
        report += """
================================================================================
SYSTEM INFORMATION
================================================================================

Platform:                   Factory Compliance Monitoring System v2.0.0
AI Engine:                  YOLOv8 (Person Detection)
Computer Vision:            OpenCV 4.x
Database:                   SQLite3
Language:                   Python 3.x
Dashboard:                  Streamlit

================================================================================
CONFIDENTIALITY NOTICE
================================================================================

This report contains confidential and proprietary information. 
Unauthorized access, use, or distribution is prohibited.
All access is logged and monitored.

================================================================================
"""
        
        # Write report
        with open(output_path, 'w', encoding="utf-8") as f:
            f.write(report)
        
        print(f"✅ Summary Report generated: {output_path}")
        return output_path
    
    @staticmethod
    def export_filtered_data(
        severity_filter: list = None,
        behavior_filter: list = None,
        start_date: str = None,
        end_date: str = None,
        format: str = 'csv'
    ) -> str:
        """
        Export filtered data based on criteria.
        
        Args:
            severity_filter: List of severity levels to include
            behavior_filter: List of behaviors to include
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            format: Output format ('csv' or 'json')
            
        Returns:
            str: Path to generated file
        """
        df = DatabaseService.get_all_violations()
        
        # Apply filters
        if severity_filter:
            df = df[df['severity'].isin(severity_filter)]
        
        if behavior_filter:
            df = df[df['behavior_class'].isin(behavior_filter)]
        
        if start_date and end_date:
            df = df[
                (df['timestamp'] >= start_date) & 
                (df['timestamp'] <= end_date)
            ]
        
        # Generate filename
        filename = f"compliance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == 'csv':
            output_path = f"outputs/reports/{filename}.csv"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            df.to_csv(output_path, index=False)
        else:  # json
            output_path = f"outputs/reports/{filename}.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            records = df.to_dict(orient='records')
            with open(output_path, 'w', encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        
        print(f"✅ Filtered export generated: {output_path}")
        return output_path
    
    @staticmethod
    def generate_daily_summary() -> dict:
        """
        Generate daily compliance summary.
        
        Returns:
            dict: Daily summary statistics
        """
        df = DatabaseService.get_all_violations()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Filter for today
        df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
        today_df = df[df['date'] == today]
        
        summary = {
            'date': today,
            'total_events': len(today_df),
            'critical': len(today_df[today_df['severity'] == 'CRITICAL']),
            'high': len(today_df[today_df['severity'] == 'HIGH']),
            'medium': len(today_df[today_df['severity'] == 'MEDIUM']),
            'low': len(today_df[today_df['severity'] == 'LOW']),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary


if __name__ == "__main__":
    # Test report generation
    print("\n📊 Generating reports...")
    
    ReportGenerator.generate_csv_report()
    ReportGenerator.generate_json_report()
    ReportGenerator.generate_summary_report()
    
    # Test filtered export
    ReportGenerator.export_filtered_data(
        severity_filter=['CRITICAL', 'HIGH'],
        format='json'
    )
    
    # Test daily summary
    daily = ReportGenerator.generate_daily_summary()
    print(f"\n📅 Daily Summary: {daily['total_events']} events today")
