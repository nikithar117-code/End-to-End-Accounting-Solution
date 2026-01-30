import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import json
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)

# ==================== DATA LOADING & VALIDATION ====================

class DataProcessor:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.validate_and_clean()
    
    def validate_and_clean(self):
        """Validate and clean the data"""
        # Convert dates
        self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
        
        # Remove rows with invalid dates
        self.df = self.df.dropna(subset=['Date'])
        
        # Ensure numeric columns are numeric
        numeric_cols = ['Transaction Amount', 'Cash Flow', 'Net Income', 'Revenue', 
                       'Expenditure', 'Profit Margin', 'Debt-to-Equity Ratio', 
                       'Operating Expenses', 'Gross Profit', 'Accuracy Score']
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Sort by date
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        print(f"Loaded {len(self.df)} valid transactions")

# ==================== TRANSACTION RECORDING MODULE ====================

class TransactionRecording:
    def __init__(self, data):
        self.df = data
    
    def get_transaction_summary(self):
        """Get summary of all transactions"""
        return {
            'total_transactions': len(self.df),
            'total_amount': round(self.df['Transaction Amount'].sum(), 2),
            'average_amount': round(self.df['Transaction Amount'].mean(), 2),
            'date_range': {
                'start': self.df['Date'].min().strftime('%Y-%m-%d'),
                'end': self.df['Date'].max().strftime('%Y-%m-%d')
            }
        }
    
    def get_transactions_by_type(self):
        """Get transactions grouped by account type"""
        grouped = self.df.groupby('Account Type').agg({
            'Transaction ID': 'count',
            'Transaction Amount': ['sum', 'mean']
        }).reset_index()
        grouped.columns = ['Account Type', 'Count', 'Total Amount', 'Average Amount']
        return grouped.to_dict('records')
    
    def create_transaction_chart(self):
        """Create transaction volume chart"""
        daily_trans = self.df.groupby(self.df['Date'].dt.date).size().reset_index()
        daily_trans.columns = ['Date', 'Count']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_trans['Date'],
            y=daily_trans['Count'],
            mode='lines+markers',
            name='Daily Transactions',
            line=dict(color='#3498db', width=2)
        ))
        
        fig.update_layout(
            title='Daily Transaction Volume',
            xaxis_title='Date',
            yaxis_title='Number of Transactions',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== FINANCIAL STATEMENTS MODULE ====================

class FinancialStatements:
    def __init__(self, data):
        self.df = data
        
    def balance_sheet(self):
        """Generate Balance Sheet"""
        asset_transactions = self.df[self.df['Account Type'] == 'Asset']
        cash = asset_transactions['Cash Flow'].sum()
        accounts_receivable = asset_transactions['Transaction Amount'].sum() * 0.15
        
        liability_transactions = self.df[self.df['Account Type'] == 'Liability']
        accounts_payable = liability_transactions['Transaction Amount'].sum()
        
        retained_earnings = self.df['Net Income'].sum()
        
        total_assets = cash + accounts_receivable
        total_liabilities = accounts_payable
        total_equity = retained_earnings
        
        return {
            'Assets': {
                'Cash': round(cash, 2),
                'Accounts Receivable': round(accounts_receivable, 2),
                'Total Assets': round(total_assets, 2)
            },
            'Liabilities': {
                'Accounts Payable': round(accounts_payable, 2),
                'Total Liabilities': round(total_liabilities, 2)
            },
            'Equity': {
                'Retained Earnings': round(retained_earnings, 2),
                'Total Equity': round(total_equity, 2)
            }
        }
    
    def profit_loss_statement(self):
        """Generate P&L Statement"""
        total_revenue = self.df['Revenue'].sum()
        operating_expenses = self.df['Operating Expenses'].sum()
        other_expenditure = self.df['Expenditure'].sum()
        total_expenses = operating_expenses + other_expenditure
        
        gross_profit = self.df['Gross Profit'].sum()
        net_income = total_revenue - total_expenses
        profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'Revenue': round(total_revenue, 2),
            'Operating Expenses': round(operating_expenses, 2),
            'Other Expenses': round(other_expenditure, 2),
            'Total Expenses': round(total_expenses, 2),
            'Gross Profit': round(gross_profit, 2),
            'Net Income': round(net_income, 2),
            'Profit Margin': round(profit_margin, 2)
        }
    
    def cash_flow_statement(self):
        """Generate Cash Flow Statement"""
        net_income = self.df['Net Income'].sum()
        changes_working_capital = self.df['Cash Flow'].sum() * 0.1
        net_cash_operations = net_income + changes_working_capital
        
        asset_purchases = self.df[self.df['Account Type'] == 'Asset']['Transaction Amount'].sum()
        capital_expenditures = -abs(asset_purchases * 0.2)
        
        debt_proceeds = self.df[self.df['Account Type'] == 'Liability']['Transaction Amount'].sum() * 0.1
        
        net_change = net_cash_operations + capital_expenditures + debt_proceeds
        beginning_balance = 50000
        ending_balance = beginning_balance + net_change
        
        return {
            'Operating Activities': round(net_cash_operations, 2),
            'Investing Activities': round(capital_expenditures, 2),
            'Financing Activities': round(debt_proceeds, 2),
            'Net Change': round(net_change, 2),
            'Beginning Balance': round(beginning_balance, 2),
            'Ending Balance': round(ending_balance, 2)
        }
    
    def create_financial_charts(self):
        """Create charts for financial statements"""
        # Revenue vs Expenses
        pl = self.profit_loss_statement()
        
        fig = go.Figure(data=[
            go.Bar(name='Revenue', x=['Financial Performance'], y=[pl['Revenue']], marker_color='#2ecc71'),
            go.Bar(name='Expenses', x=['Financial Performance'], y=[pl['Total Expenses']], marker_color='#e74c3c'),
            go.Bar(name='Net Income', x=['Financial Performance'], y=[pl['Net Income']], marker_color='#3498db')
        ])
        
        fig.update_layout(
            title='Revenue, Expenses, and Net Income',
            yaxis_title='Amount',
            barmode='group',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== SUBSIDIARY LEDGERS MODULE ====================

class SubsidiaryLedgers:
    def __init__(self, data):
        self.df = data
    
    def accounts_receivable(self):
        """Calculate Accounts Receivable"""
        asset_trans = self.df[self.df['Account Type'] == 'Asset']
        total_ar = asset_trans['Transaction Amount'].sum() * 0.15
        
        return {
            'total_receivable': round(total_ar, 2),
            'number_of_transactions': len(asset_trans),
            'average_receivable': round(total_ar / len(asset_trans), 2) if len(asset_trans) > 0 else 0
        }
    
    def accounts_payable(self):
        """Calculate Accounts Payable"""
        liability_trans = self.df[self.df['Account Type'] == 'Liability']
        total_ap = liability_trans['Transaction Amount'].sum()
        
        return {
            'total_payable': round(total_ap, 2),
            'number_of_transactions': len(liability_trans),
            'average_payable': round(total_ap / len(liability_trans), 2) if len(liability_trans) > 0 else 0
        }
    
    def fixed_assets(self):
        """Calculate Fixed Assets"""
        asset_trans = self.df[self.df['Account Type'] == 'Asset']
        total_assets = asset_trans['Transaction Amount'].sum()
        
        return {
            'total_fixed_assets': round(total_assets, 2),
            'number_of_assets': len(asset_trans),
            'average_asset_value': round(total_assets / len(asset_trans), 2) if len(asset_trans) > 0 else 0
        }
    
    def create_ledger_chart(self):
        """Create chart for subsidiary ledgers"""
        ar = self.accounts_receivable()
        ap = self.accounts_payable()
        fa = self.fixed_assets()
        
        fig = go.Figure(data=[
            go.Bar(x=['Accounts Receivable', 'Accounts Payable', 'Fixed Assets'],
                   y=[ar['total_receivable'], ap['total_payable'], fa['total_fixed_assets']],
                   marker_color=['#3498db', '#e74c3c', '#2ecc71'])
        ])
        
        fig.update_layout(
            title='Subsidiary Ledgers Overview',
            yaxis_title='Amount',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== BANK AND CASH MANAGEMENT MODULE ====================

class BankCashManagement:
    def __init__(self, data):
        self.df = data
    
    def cash_summary(self):
        """Get cash summary"""
        total_cash_flow = self.df['Cash Flow'].sum()
        positive_flow = self.df[self.df['Cash Flow'] > 0]['Cash Flow'].sum()
        negative_flow = self.df[self.df['Cash Flow'] < 0]['Cash Flow'].sum()
        
        return {
            'total_cash_flow': round(total_cash_flow, 2),
            'cash_inflow': round(positive_flow, 2),
            'cash_outflow': round(abs(negative_flow), 2),
            'net_cash': round(total_cash_flow, 2)
        }
    
    def bank_reconciliation(self):
        """Perform bank reconciliation"""
        book_balance = self.df['Cash Flow'].sum()
        outstanding_checks = self.df[self.df['Transaction Outcome'] == 'Failed']['Transaction Amount'].sum()
        deposits_in_transit = self.df['Transaction Amount'].sum() * 0.02
        
        adjusted_balance = book_balance - outstanding_checks + deposits_in_transit
        
        return {
            'book_balance': round(book_balance, 2),
            'outstanding_checks': round(outstanding_checks, 2),
            'deposits_in_transit': round(deposits_in_transit, 2),
            'adjusted_balance': round(adjusted_balance, 2)
        }
    
    def create_cash_flow_chart(self):
        """Create cash flow chart"""
        daily_cash = self.df.groupby(self.df['Date'].dt.date)['Cash Flow'].sum().reset_index()
        daily_cash.columns = ['Date', 'Cash Flow']
        daily_cash['Cumulative'] = daily_cash['Cash Flow'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_cash['Date'],
            y=daily_cash['Cumulative'],
            mode='lines',
            name='Cumulative Cash Flow',
            fill='tozeroy',
            line=dict(color='#2ecc71', width=2)
        ))
        
        fig.update_layout(
            title='Cumulative Cash Flow Over Time',
            xaxis_title='Date',
            yaxis_title='Cash Flow',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== REPORTING AND ANALYSIS MODULE ====================

class ReportingAnalysis:
    def __init__(self, data):
        self.df = data
    
    def key_metrics(self):
        """Calculate key financial metrics"""
        total_revenue = self.df['Revenue'].sum()
        total_expenses = self.df['Expenditure'].sum() + self.df['Operating Expenses'].sum()
        net_profit = self.df['Net Income'].sum()
        
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        total_transactions = len(self.df)
        successful = (self.df['Transaction Outcome'] == 'Success').sum()
        success_rate = (successful / total_transactions * 100) if total_transactions > 0 else 0
        
        return {
            'Total Revenue': round(total_revenue, 2),
            'Total Expenses': round(total_expenses, 2),
            'Net Profit': round(net_profit, 2),
            'Profit Margin': round(profit_margin, 2),
            'Debt-to-Equity Ratio': round(self.df['Debt-to-Equity Ratio'].mean(), 2),
            'Success Rate': round(success_rate, 2),
            'Total Transactions': total_transactions
        }
    
    def monthly_trends(self):
        """Calculate monthly trends"""
        monthly = self.df.groupby(self.df['Date'].dt.to_period('M')).agg({
            'Revenue': 'sum',
            'Expenditure': 'sum',
            'Net Income': 'sum',
            'Transaction ID': 'count'
        }).reset_index()
        
        monthly['Period'] = monthly['Period'].astype(str)
        monthly.columns = ['Period', 'Revenue', 'Expenses', 'Net Income', 'Transactions']
        
        return monthly.to_dict('records')
    
    def create_analysis_charts(self):
        """Create analysis charts"""
        monthly = self.monthly_trends()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[m['Period'] for m in monthly],
            y=[m['Revenue'] for m in monthly],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#2ecc71', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=[m['Period'] for m in monthly],
            y=[m['Expenses'] for m in monthly],
            mode='lines+markers',
            name='Expenses',
            line=dict(color='#e74c3c', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=[m['Period'] for m in monthly],
            y=[m['Net Income'] for m in monthly],
            mode='lines+markers',
            name='Net Income',
            line=dict(color='#3498db', width=2)
        ))
        
        fig.update_layout(
            title='Monthly Financial Trends',
            xaxis_title='Period',
            yaxis_title='Amount',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== TAX MANAGEMENT MODULE ====================

class TaxManagement:
    def __init__(self, data):
        self.df = data
    
    def calculate_taxes(self):
        """Calculate tax liabilities"""
        taxable_income = self.df['Net Income'].sum()
        
        # Assuming 30% corporate tax rate
        income_tax = taxable_income * 0.30
        
        # VAT/GST on revenue (assuming 10%)
        vat_collected = self.df['Revenue'].sum() * 0.10
        vat_paid = self.df['Expenditure'].sum() * 0.10
        vat_payable = vat_collected - vat_paid
        
        total_tax = income_tax + vat_payable
        
        return {
            'taxable_income': round(taxable_income, 2),
            'income_tax': round(income_tax, 2),
            'vat_collected': round(vat_collected, 2),
            'vat_paid': round(vat_paid, 2),
            'vat_payable': round(vat_payable, 2),
            'total_tax_liability': round(total_tax, 2)
        }
    
    def quarterly_tax_summary(self):
        """Get quarterly tax summary"""
        quarterly = self.df.groupby(self.df['Date'].dt.to_period('Q')).agg({
            'Net Income': 'sum',
            'Revenue': 'sum',
            'Expenditure': 'sum'
        }).reset_index()
        
        quarterly['Period'] = quarterly['Period'].astype(str)
        quarterly['Income Tax'] = quarterly['Net Income'] * 0.30
        quarterly['VAT Payable'] = (quarterly['Revenue'] - quarterly['Expenditure']) * 0.10
        quarterly['Total Tax'] = quarterly['Income Tax'] + quarterly['VAT Payable']
        
        return quarterly[['Period', 'Income Tax', 'VAT Payable', 'Total Tax']].to_dict('records')
    
    def create_tax_chart(self):
        """Create tax visualization"""
        taxes = self.calculate_taxes()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['Income Tax', 'VAT Payable'],
                values=[taxes['income_tax'], taxes['vat_payable']],
                marker=dict(colors=['#3498db', '#e74c3c'])
            )
        ])
        
        fig.update_layout(
            title='Tax Liability Breakdown',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== BUDGETING AND FORECASTING MODULE ====================

class BudgetingForecasting:
    def __init__(self, data):
        self.df = data
    
    def budget_analysis(self):
        """Perform budget vs actual analysis"""
        actual_revenue = self.df['Revenue'].sum()
        actual_expenses = self.df['Expenditure'].sum() + self.df['Operating Expenses'].sum()
        
        # Assuming budget is 10% higher than actual
        budget_revenue = actual_revenue * 1.10
        budget_expenses = actual_expenses * 0.90
        
        revenue_variance = actual_revenue - budget_revenue
        expense_variance = actual_expenses - budget_expenses
        
        return {
            'budget_revenue': round(budget_revenue, 2),
            'actual_revenue': round(actual_revenue, 2),
            'revenue_variance': round(revenue_variance, 2),
            'revenue_variance_pct': round((revenue_variance / budget_revenue * 100), 2),
            'budget_expenses': round(budget_expenses, 2),
            'actual_expenses': round(actual_expenses, 2),
            'expense_variance': round(expense_variance, 2),
            'expense_variance_pct': round((expense_variance / budget_expenses * 100), 2)
        }
    
    def forecast_next_quarter(self):
        """Forecast next quarter performance"""
        # Calculate average growth rate
        monthly = self.df.groupby(self.df['Date'].dt.to_period('M')).agg({
            'Revenue': 'sum',
            'Expenditure': 'sum',
            'Net Income': 'sum'
        })
        
        avg_revenue = monthly['Revenue'].mean()
        avg_expenses = monthly['Expenditure'].mean()
        
        # Project for 3 months
        forecast_revenue = avg_revenue * 3 * 1.05  # 5% growth
        forecast_expenses = avg_expenses * 3 * 1.03  # 3% increase
        forecast_profit = forecast_revenue - forecast_expenses
        
        return {
            'forecast_revenue': round(forecast_revenue, 2),
            'forecast_expenses': round(forecast_expenses, 2),
            'forecast_profit': round(forecast_profit, 2),
            'forecast_margin': round((forecast_profit / forecast_revenue * 100), 2)
        }
    
    def create_forecast_chart(self):
        """Create forecast visualization"""
        forecast = self.forecast_next_quarter()
        
        fig = go.Figure(data=[
            go.Bar(
                x=['Forecasted Revenue', 'Forecasted Expenses', 'Forecasted Profit'],
                y=[forecast['forecast_revenue'], forecast['forecast_expenses'], forecast['forecast_profit']],
                marker_color=['#2ecc71', '#e74c3c', '#3498db']
            )
        ])
        
        fig.update_layout(
            title='Next Quarter Forecast',
            yaxis_title='Amount',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== COMPLIANCE AND CONTROLS MODULE ====================

class ComplianceControls:
    def __init__(self, data):
        self.df = data
    
    def data_quality_check(self):
        """Check data quality and compliance"""
        total_records = len(self.df)
        missing_data = self.df.isnull().sum().sum()
        duplicate_transactions = self.df.duplicated(subset=['Transaction ID']).sum()
        
        accuracy_avg = self.df['Accuracy Score'].mean()
        low_accuracy = (self.df['Accuracy Score'] < 0.8).sum()
        
        return {
            'total_records': total_records,
            'missing_data_points': int(missing_data),
            'duplicate_transactions': int(duplicate_transactions),
            'average_accuracy': round(accuracy_avg * 100, 2),
            'low_accuracy_count': int(low_accuracy),
            'data_quality_score': round((1 - (missing_data + duplicate_transactions) / (total_records * len(self.df.columns))) * 100, 2)
        }
    
    def transaction_audit(self):
        """Audit transaction compliance"""
        failed_transactions = (self.df['Transaction Outcome'] == 'Failed').sum()
        success_rate = ((self.df['Transaction Outcome'] == 'Success').sum() / len(self.df)) * 100
        
        # Check for unusual transactions (>3 std dev)
        mean_amount = self.df['Transaction Amount'].mean()
        std_amount = self.df['Transaction Amount'].std()
        unusual_transactions = ((self.df['Transaction Amount'] > mean_amount + 3*std_amount) | 
                               (self.df['Transaction Amount'] < mean_amount - 3*std_amount)).sum()
        
        return {
            'total_transactions': len(self.df),
            'failed_transactions': int(failed_transactions),
            'success_rate': round(success_rate, 2),
            'unusual_transactions': int(unusual_transactions),
            'compliance_score': round(success_rate, 2)
        }
    
    def create_compliance_chart(self):
        """Create compliance visualization"""
        audit = self.transaction_audit()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['Successful', 'Failed'],
                values=[audit['total_transactions'] - audit['failed_transactions'], audit['failed_transactions']],
                marker=dict(colors=['#2ecc71', '#e74c3c'])
            )
        ])
        
        fig.update_layout(
            title='Transaction Success Rate',
            template='plotly_white'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)

# ==================== FLASK ROUTES ====================

# Load data globally
csv_path = r"C:\Users\Kishore\Downloads\archive (8)\accounting_data.csv"
processor = DataProcessor(csv_path)

@app.route('/')
def dashboard():
    """Main dashboard"""
    financials = FinancialStatements(processor.df)
    reporting = ReportingAnalysis(processor.df)
    
    metrics = reporting.key_metrics()
    
    return render_template_string(MAIN_DASHBOARD_TEMPLATE,
                                 metrics=metrics,
                                 timestamp=datetime.now().strftime('%B %d, %Y at %I:%M %p'))

@app.route('/transaction-recording')
def transaction_recording():
    """Transaction Recording page"""
    trans_rec = TransactionRecording(processor.df)
    
    summary = trans_rec.get_transaction_summary()
    by_type = trans_rec.get_transactions_by_type()
    chart = trans_rec.create_transaction_chart()
    
    return render_template_string(TRANSACTION_RECORDING_TEMPLATE,
                                 summary=summary,
                                 by_type=by_type,
                                 chart=chart)

@app.route('/financial-statements')
def financial_statements():
    """Financial Statements page"""
    financials = FinancialStatements(processor.df)
    
    balance_sheet = financials.balance_sheet()
    pl_statement = financials.profit_loss_statement()
    cash_flow = financials.cash_flow_statement()
    chart = financials.create_financial_charts()
    
    return render_template_string(FINANCIAL_STATEMENTS_TEMPLATE,
                                 balance_sheet=balance_sheet,
                                 pl_statement=pl_statement,
                                 cash_flow=cash_flow,
                                 chart=chart)

@app.route('/subsidiary-ledgers')
def subsidiary_ledgers():
    """Subsidiary Ledgers page"""
    ledgers = SubsidiaryLedgers(processor.df)
    
    ar = ledgers.accounts_receivable()
    ap = ledgers.accounts_payable()
    fa = ledgers.fixed_assets()
    chart = ledgers.create_ledger_chart()
    
    return render_template_string(SUBSIDIARY_LEDGERS_TEMPLATE,
                                 ar=ar, ap=ap, fa=fa, chart=chart)

@app.route('/bank-cash-management')
def bank_cash_management():
    """Bank and Cash Management page"""
    bank_cash = BankCashManagement(processor.df)
    
    cash_summary = bank_cash.cash_summary()
    reconciliation = bank_cash.bank_reconciliation()
    chart = bank_cash.create_cash_flow_chart()
    
    return render_template_string(BANK_CASH_TEMPLATE,
                                 cash_summary=cash_summary,
                                 reconciliation=reconciliation,
                                 chart=chart)

@app.route('/reporting-analysis')
def reporting_analysis():
    """Reporting and Analysis page"""
    reporting = ReportingAnalysis(processor.df)
    
    metrics = reporting.key_metrics()
    trends = reporting.monthly_trends()
    chart = reporting.create_analysis_charts()
    
    return render_template_string(REPORTING_ANALYSIS_TEMPLATE,
                                 metrics=metrics,
                                 trends=trends,
                                 chart=chart)

@app.route('/tax-management')
def tax_management():
    """Tax Management page"""
    tax_mgmt = TaxManagement(processor.df)
    
    taxes = tax_mgmt.calculate_taxes()
    quarterly = tax_mgmt.quarterly_tax_summary()
    chart = tax_mgmt.create_tax_chart()
    
    return render_template_string(TAX_MANAGEMENT_TEMPLATE,
                                 taxes=taxes,
                                 quarterly=quarterly,
                                 chart=chart)

@app.route('/budgeting-forecasting')
def budgeting_forecasting():
    """Budgeting and Forecasting page"""
    budget = BudgetingForecasting(processor.df)
    
    budget_analysis = budget.budget_analysis()
    forecast = budget.forecast_next_quarter()
    chart = budget.create_forecast_chart()
    
    return render_template_string(BUDGETING_FORECASTING_TEMPLATE,
                                 budget_analysis=budget_analysis,
                                 forecast=forecast,
                                 chart=chart)

@app.route('/compliance-controls')
def compliance_controls():
    """Compliance and Controls page"""
    compliance = ComplianceControls(processor.df)
    
    quality = compliance.data_quality_check()
    audit = compliance.transaction_audit()
    chart = compliance.create_compliance_chart()
    
    return render_template_string(COMPLIANCE_CONTROLS_TEMPLATE,
                                 quality=quality,
                                 audit=audit,
                                 chart=chart)

# ==================== HTML TEMPLATES ====================

MAIN_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accounting Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .header h1 { color: #2c3e50; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #7f8c8d; font-size: 1.1em; }
        .button-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .category-button { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); cursor: pointer; transition: all 0.3s; text-decoration: none; display: block; }
        .category-button:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
        .category-button h3 { color: #2c3e50; margin-bottom: 10px; font-size: 1.3em; }
        .category-button p { color: #7f8c8d; font-size: 0.9em; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .metric-card h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .metric-card .value { color: #2c3e50; font-size: 2em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Accounting Management System</h1>
            <p>Comprehensive End-to-End Accounting Solution</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Last Updated: {{ timestamp }}</p>
        </div>
        
        <div class="button-grid">
            <a href="/transaction-recording" class="category-button">
                <h3>📝 Transaction Recording</h3>
                <p>Record and manage all financial transactions</p>
            </a>
            
            <a href="/financial-statements" class="category-button">
                <h3>📈 Core Financial Statements</h3>
                <p>Balance Sheet, P&L, Cash Flow</p>
            </a>
            
            <a href="/subsidiary-ledgers" class="category-button">
                <h3>📚 Subsidiary Ledgers</h3>
                <p>Accounts Receivable, Payable, Fixed Assets</p>
            </a>
            
            <a href="/bank-cash-management" class="category-button">
                <h3>🏦 Bank and Cash Management</h3>
                <p>Cash flow tracking and bank reconciliation</p>
            </a>
            
            <a href="/reporting-analysis" class="category-button">
                <h3>📊 Reporting and Analysis</h3>
                <p>Financial metrics and trend analysis</p>
            </a>
            
            <a href="/tax-management" class="category-button">
                <h3>💰 Tax Management</h3>
                <p>Tax calculations and compliance</p>
            </a>
            
            <a href="/budgeting-forecasting" class="category-button">
                <h3>🎯 Budgeting and Forecasting</h3>
                <p>Budget analysis and financial forecasting</p>
            </a>
            
            <a href="/compliance-controls" class="category-button">
                <h3>✅ Compliance and Controls</h3>
                <p>Data quality and audit controls</p>
            </a>
        </div>
        
        <div class="header">
            <h2 style="margin-bottom: 20px;">Key Metrics Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>Total Revenue</h4>
                    <div class="value">${{ metrics['Total Revenue'] }}</div>
                </div>
                <div class="metric-card">
                    <h4>Net Profit</h4>
                    <div class="value">${{ metrics['Net Profit'] }}</div>
                </div>
                <div class="metric-card">
                    <h4>Profit Margin</h4>
                    <div class="value">{{ metrics['Profit Margin'] }}%</div>
                </div>
                <div class="metric-card">
                    <h4>Success Rate</h4>
                    <div class="value">{{ metrics['Success Rate'] }}%</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

TRANSACTION_RECORDING_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transaction Recording</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .back-button:hover { background: #2980b9; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .stat-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .stat-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📝 Transaction Recording</h1>
            <p>Comprehensive transaction management and tracking</p>
        </div>
        
        <div class="content-card">
            <h2>Transaction Summary</h2>
            <div class="stats-grid">
                <div class="stat-box">
                    <h4>Total Transactions</h4>
                    <div class="value">{{ summary.total_transactions }}</div>
                </div>
                <div class="stat-box">
                    <h4>Total Amount</h4>
                    <div class="value">${{ summary.total_amount }}</div>
                </div>
                <div class="stat-box">
                    <h4>Average Amount</h4>
                    <div class="value">${{ summary.average_amount }}</div>
                </div>
                <div class="stat-box">
                    <h4>Date Range</h4>
                    <div class="value" style="font-size: 1em;">{{ summary.date_range.start }} to {{ summary.date_range.end }}</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Transactions by Account Type</h2>
            <table>
                <tr>
                    <th>Account Type</th>
                    <th>Count</th>
                    <th>Total Amount</th>
                    <th>Average Amount</th>
                </tr>
                {% for item in by_type %}
                <tr>
                    <td>{{ item['Account Type'] }}</td>
                    <td>{{ item['Count'] }}</td>
                    <td>${{ item['Total Amount'] }}</td>
                    <td>${{ item['Average Amount'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="content-card">
            <h2>Transaction Volume Chart</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

FINANCIAL_STATEMENTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Statements</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .statement-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .statement-section { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .statement-section h3 { color: #2c3e50; margin-bottom: 15px; }
        .line-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ddd; }
        .line-item.total { font-weight: bold; border-top: 2px solid #2c3e50; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📈 Core Financial Statements</h1>
            <p>Balance Sheet, Profit & Loss, and Cash Flow Statement</p>
        </div>
        
        <div class="content-card">
            <h2>Balance Sheet</h2>
            <div class="statement-grid">
                <div class="statement-section">
                    <h3>Assets</h3>
                    <div class="line-item">
                        <span>Cash</span>
                        <span>${{ balance_sheet.Assets.Cash }}</span>
                    </div>
                    <div class="line-item">
                        <span>Accounts Receivable</span>
                        <span>${{ balance_sheet.Assets['Accounts Receivable'] }}</span>
                    </div>
                    <div class="line-item total">
                        <span>Total Assets</span>
                        <span>${{ balance_sheet.Assets['Total Assets'] }}</span>
                    </div>
                </div>
                
                <div class="statement-section">
                    <h3>Liabilities</h3>
                    <div class="line-item">
                        <span>Accounts Payable</span>
                        <span>${{ balance_sheet.Liabilities['Accounts Payable'] }}</span>
                    </div>
                    <div class="line-item total">
                        <span>Total Liabilities</span>
                        <span>${{ balance_sheet.Liabilities['Total Liabilities'] }}</span>
                    </div>
                </div>
                
                <div class="statement-section">
                    <h3>Equity</h3>
                    <div class="line-item">
                        <span>Retained Earnings</span>
                        <span>${{ balance_sheet.Equity['Retained Earnings'] }}</span>
                    </div>
                    <div class="line-item total">
                        <span>Total Equity</span>
                        <span>${{ balance_sheet.Equity['Total Equity'] }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Profit & Loss Statement</h2>
            <div class="statement-section">
                <div class="line-item">
                    <span>Revenue</span>
                    <span>${{ pl_statement.Revenue }}</span>
                </div>
                <div class="line-item">
                    <span>Operating Expenses</span>
                    <span>${{ pl_statement['Operating Expenses'] }}</span>
                </div>
                <div class="line-item">
                    <span>Other Expenses</span>
                    <span>${{ pl_statement['Other Expenses'] }}</span>
                </div>
                <div class="line-item total">
                    <span>Total Expenses</span>
                    <span>${{ pl_statement['Total Expenses'] }}</span>
                </div>
                <div class="line-item">
                    <span>Gross Profit</span>
                    <span>${{ pl_statement['Gross Profit'] }}</span>
                </div>
                <div class="line-item total">
                    <span>Net Income</span>
                    <span>${{ pl_statement['Net Income'] }}</span>
                </div>
                <div class="line-item">
                    <span>Profit Margin</span>
                    <span>{{ pl_statement['Profit Margin'] }}%</span>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Cash Flow Statement</h2>
            <div class="statement-section">
                <div class="line-item">
                    <span>Operating Activities</span>
                    <span>${{ cash_flow['Operating Activities'] }}</span>
                </div>
                <div class="line-item">
                    <span>Investing Activities</span>
                    <span>${{ cash_flow['Investing Activities'] }}</span>
                </div>
                <div class="line-item">
                    <span>Financing Activities</span>
                    <span>${{ cash_flow['Financing Activities'] }}</span>
                </div>
                <div class="line-item total">
                    <span>Net Change in Cash</span>
                    <span>${{ cash_flow['Net Change'] }}</span>
                </div>
                <div class="line-item">
                    <span>Beginning Balance</span>
                    <span>${{ cash_flow['Beginning Balance'] }}</span>
                </div>
                <div class="line-item total">
                    <span>Ending Balance</span>
                    <span>${{ cash_flow['Ending Balance'] }}</span>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Financial Performance Chart</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

SUBSIDIARY_LEDGERS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subsidiary Ledgers</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .ledger-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .ledger-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .ledger-box h3 { color: #2c3e50; margin-bottom: 15px; }
        .ledger-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📚 Subsidiary Ledgers</h1>
            <p>Accounts Receivable, Accounts Payable, and Fixed Assets</p>
        </div>
        
        <div class="content-card">
            <h2>Ledger Summary</h2>
            <div class="ledger-grid">
                <div class="ledger-box">
                    <h3>Accounts Receivable</h3>
                    <div class="ledger-item">
                        <span>Total Receivable</span>
                        <span>${{ ar.total_receivable }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Number of Transactions</span>
                        <span>{{ ar.number_of_transactions }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Average Receivable</span>
                        <span>${{ ar.average_receivable }}</span>
                    </div>
                </div>
                
                <div class="ledger-box">
                    <h3>Accounts Payable</h3>
                    <div class="ledger-item">
                        <span>Total Payable</span>
                        <span>${{ ap.total_payable }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Number of Transactions</span>
                        <span>{{ ap.number_of_transactions }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Average Payable</span>
                        <span>${{ ap.average_payable }}</span>
                    </div>
                </div>
                
                <div class="ledger-box">
                    <h3>Fixed Assets</h3>
                    <div class="ledger-item">
                        <span>Total Fixed Assets</span>
                        <span>${{ fa.total_fixed_assets }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Number of Assets</span>
                        <span>{{ fa.number_of_assets }}</span>
                    </div>
                    <div class="ledger-item">
                        <span>Average Asset Value</span>
                        <span>${{ fa.average_asset_value }}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Ledgers Overview Chart</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

BANK_CASH_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank and Cash Management</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .cash-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .cash-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .cash-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .cash-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>🏦 Bank and Cash Management</h1>
            <p>Cash flow tracking and bank reconciliation</p>
        </div>
        
        <div class="content-card">
            <h2>Cash Summary</h2>
            <div class="cash-grid">
                <div class="cash-box">
                    <h4>Total Cash Flow</h4>
                    <div class="value">${{ cash_summary.total_cash_flow }}</div>
                </div>
                <div class="cash-box">
                    <h4>Cash Inflow</h4>
                    <div class="value" style="color: #2ecc71;">${{ cash_summary.cash_inflow }}</div>
                </div>
                <div class="cash-box">
                    <h4>Cash Outflow</h4>
                    <div class="value" style="color: #e74c3c;">${{ cash_summary.cash_outflow }}</div>
                </div>
                <div class="cash-box">
                    <h4>Net Cash</h4>
                    <div class="value">${{ cash_summary.net_cash }}</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Bank Reconciliation</h2>
            <div class="cash-grid">
                <div class="cash-box">
                    <h4>Book Balance</h4>
                    <div class="value">${{ reconciliation.book_balance }}</div>
                </div>
                <div class="cash-box">
                    <h4>Outstanding Checks</h4>
                    <div class="value">${{ reconciliation.outstanding_checks }}</div>
                </div>
                <div class="cash-box">
                    <h4>Deposits in Transit</h4>
                    <div class="value">${{ reconciliation.deposits_in_transit }}</div>
                </div>
                <div class="cash-box">
                    <h4>Adjusted Balance</h4>
                    <div class="value">${{ reconciliation.adjusted_balance }}</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Cash Flow Trend</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

REPORTING_ANALYSIS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporting and Analysis</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .metric-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .metric-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .metric-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📊 Reporting and Analysis</h1>
            <p>Comprehensive financial metrics and trend analysis</p>
        </div>
        
        <div class="content-card">
            <h2>Key Financial Metrics</h2>
            <div class="metrics-grid">
                {% for key, value in metrics.items() %}
                <div class="metric-box">
                    <h4>{{ key }}</h4>
                    <div class="value">
                        {% if '%' in key or 'Ratio' in key %}
                            {{ value }}{% if 'Ratio' not in key %}%{% endif %}
                        {% else %}
                            ${{ value }}
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="content-card">
            <h2>Monthly Trends</h2>
            <table>
                <tr>
                    <th>Period</th>
                    <th>Revenue</th>
                    <th>Expenses</th>
                    <th>Net Income</th>
                    <th>Transactions</th>
                </tr>
                {% for trend in trends %}
                <tr>
                    <td>{{ trend.Period }}</td>
                    <td>${{ trend.Revenue }}</td>
                    <td>${{ trend.Expenses }}</td>
                    <td>${{ trend['Net Income'] }}</td>
                    <td>{{ trend.Transactions }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="content-card">
            <h2>Financial Trends Chart</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

TAX_MANAGEMENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tax Management</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .tax-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .tax-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .tax-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .tax-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>💰 Tax Management</h1>
            <p>Tax calculations and compliance tracking</p>
        </div>
        
        <div class="content-card">
            <h2>Tax Summary</h2>
            <div class="tax-grid">
                <div class="tax-box">
                    <h4>Taxable Income</h4>
                    <div class="value">${{ taxes.taxable_income }}</div>
                </div>
                <div class="tax-box">
                    <h4>Income Tax</h4>
                    <div class="value">${{ taxes.income_tax }}</div>
                </div>
                <div class="tax-box">
                    <h4>VAT Payable</h4>
                    <div class="value">${{ taxes.vat_payable }}</div>
                </div>
                <div class="tax-box">
                    <h4>Total Tax Liability</h4>
                    <div class="value">${{ taxes.total_tax_liability }}</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Quarterly Tax Summary</h2>
            <table>
                <tr>
                    <th>Period</th>
                    <th>Income Tax</th>
                    <th>VAT Payable</th>
                    <th>Total Tax</th>
                </tr>
                {% for q in quarterly %}
                <tr>
                    <td>{{ q.Period }}</td>
                    <td>${{ q['Income Tax'] }}</td>
                    <td>${{ q['VAT Payable'] }}</td>
                    <td>${{ q['Total Tax'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <div class="content-card">
            <h2>Tax Breakdown</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

BUDGETING_FORECASTING_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Budgeting and Forecasting</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .budget-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .budget-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .budget-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .budget-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
        .positive { color: #2ecc71 !important; }
        .negative { color: #e74c3c !important; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>🎯 Budgeting and Forecasting</h1>
            <p>Budget analysis and financial projections</p>
        </div>
        
        <div class="content-card">
            <h2>Budget vs Actual Analysis</h2>
            <div class="budget-grid">
                <div class="budget-box">
                    <h4>Budget Revenue</h4>
                    <div class="value">${{ budget_analysis.budget_revenue }}</div>
                </div>
                <div class="budget-box">
                    <h4>Actual Revenue</h4>
                    <div class="value">${{ budget_analysis.actual_revenue }}</div>
                </div>
                <div class="budget-box">
                    <h4>Revenue Variance</h4>
                    <div class="value {% if budget_analysis.revenue_variance > 0 %}positive{% else %}negative{% endif %}">
                        ${{ budget_analysis.revenue_variance }} ({{ budget_analysis.revenue_variance_pct }}%)
                    </div>
                </div>
                <div class="budget-box">
                    <h4>Budget Expenses</h4>
                    <div class="value">${{ budget_analysis.budget_expenses }}</div>
                </div>
                <div class="budget-box">
                    <h4>Actual Expenses</h4>
                    <div class="value">${{ budget_analysis.actual_expenses }}</div>
                </div>
                <div class="budget-box">
                    <h4>Expense Variance</h4>
                    <div class="value {% if budget_analysis.expense_variance < 0 %}positive{% else %}negative{% endif %}">
                        ${{ budget_analysis.expense_variance }} ({{ budget_analysis.expense_variance_pct }}%)
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Next Quarter Forecast</h2>
            <div class="budget-grid">
                <div class="budget-box">
                    <h4>Forecast Revenue</h4>
                    <div class="value">${{ forecast.forecast_revenue }}</div>
                </div>
                <div class="budget-box">
                    <h4>Forecast Expenses</h4>
                    <div class="value">${{ forecast.forecast_expenses }}</div>
                </div>
                <div class="budget-box">
                    <h4>Forecast Profit</h4>
                    <div class="value positive">${{ forecast.forecast_profit }}</div>
                </div>
                <div class="budget-box">
                    <h4>Forecast Margin</h4>
                    <div class="value">{{ forecast.forecast_margin }}%</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Forecast Visualization</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

COMPLIANCE_CONTROLS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance and Controls</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .back-button { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px; }
        .content-card { background: white; padding: 30px; border-radius: 15px; margin-bottom: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .compliance-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .compliance-box { background: #f8f9fa; padding: 20px; border-radius: 10px; }
        .compliance-box h4 { color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }
        .compliance-box .value { color: #2c3e50; font-size: 1.8em; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← Back to Dashboard</a>
        
        <div class="header">
            <h1>✅ Compliance and Controls</h1>
            <p>Data quality checks and audit controls</p>
        </div>
        
        <div class="content-card">
            <h2>Data Quality Assessment</h2>
            <div class="compliance-grid">
                <div class="compliance-box">
                    <h4>Total Records</h4>
                    <div class="value">{{ quality.total_records }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Missing Data Points</h4>
                    <div class="value">{{ quality.missing_data_points }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Duplicate Transactions</h4>
                    <div class="value">{{ quality.duplicate_transactions }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Average Accuracy</h4>
                    <div class="value">{{ quality.average_accuracy }}%</div>
                </div>
                <div class="compliance-box">
                    <h4>Low Accuracy Count</h4>
                    <div class="value">{{ quality.low_accuracy_count }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Data Quality Score</h4>
                    <div class="value">{{ quality.data_quality_score }}%</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Transaction Audit</h2>
            <div class="compliance-grid">
                <div class="compliance-box">
                    <h4>Total Transactions</h4>
                    <div class="value">{{ audit.total_transactions }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Failed Transactions</h4>
                    <div class="value">{{ audit.failed_transactions }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Success Rate</h4>
                    <div class="value">{{ audit.success_rate }}%</div>
                </div>
                <div class="compliance-box">
                    <h4>Unusual Transactions</h4>
                    <div class="value">{{ audit.unusual_transactions }}</div>
                </div>
                <div class="compliance-box">
                    <h4>Compliance Score</h4>
                    <div class="value">{{ audit.compliance_score }}%</div>
                </div>
            </div>
        </div>
        
        <div class="content-card">
            <h2>Transaction Success Rate</h2>
            <div id="chart"></div>
        </div>
    </div>
    
    <script>
        var chartData = {{ chart|safe }};
        Plotly.newPlot('chart', chartData.data, chartData.layout);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, port=5000)