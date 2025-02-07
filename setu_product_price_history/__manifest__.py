{
    'name': 'Product Price History in Sales & Purchase',
    

    'description': """
        Setu Product Price History in Sales & Purchase enable users to Unlock smarter, faster, and more profitable pricing decisions every time you buy or sell. The Setu Product Price History Application 
        integrates seamlessly into your workflow, providing instant access to past purchase and sales order details without saving the record. From historical purchase prices to previous sales trends, this 
        application empowers businesses to make informed decisions that drive profitability and efficiency.
    """,
    
    'summary': """
        Product Price History in Sales & Purchase, realtime price history, sales purchase price history, sales price history, purchase price history,Sales price history,
    Purchase price history,Pricing decisions,Sales order history,Purchase order tracking,Supplier price comparison,Product cost analysis,Profit margin optimization,Real-time pricing insights,
    Historical data analysis,Automated price tracking,Inventory cost management,Stock valuation,Procurement efficiency,Cash flow optimization,Cost control strategies,Dynamic pricing management,
    Vendor performance analysis,Unit cost tracking,Customer-specific pricing,Expense management,Accounting integration,Financial forecasting,Competitive pricing strategy,Inventory turnover analysis,
    Stock movement tracking,Revenue optimization,Purchase cost forecasting,Cash management in procurement,Accounts payable insights,Sales and inventory reconciliation,Warehouse stock valuation,
    Budget-friendly procurement,Cost-saving analytics,Order cycle analysis, advance inventory report, abc sales analysis reports, dashboard, shopify, woocommerce, wayfair, access right management, 
    cash forecast, inventory count, inventory ledger, rfm analysis, rma, The Product Sales & Purchase Price History application in Odoo ERP provides real-time access to sales order history and purchase 
    order tracking, helping businesses make data-driven pricing decisions. When creating a sales order, users can view previous sales prices, customer-specific pricing, and profit margins. During purchase 
    order creation, past supplier prices, purchase quantities, and unit costs are displayed for better cost control and procurement efficiency. The system enables inventory cost management, stock valuation, 
    and vendor performance analysis, ensuring optimized cash flow and financial forecasting. By integrating historical data analysis, businesses can improve expense management, enhance competitive pricing 
    strategies, and achieve cost-saving analytics. The app also supports automated price tracking, order cycle analysis, and warehouse stock valuation, making it an essential tool for revenue optimization 
    and budget-friendly procurement. With real-time pricing insights, companies can streamline inventory turnover analysis and maintain accurate sales and inventory reconciliation.
        """,

    'author': 'Setu Consulting Services Pvt. Ltd.',
    'website': 'https://www.setuconsulting.com',
    'category': 'Uncategorized',
    'version': '1.0',

    'images': ['static/description/banner.gif'],
    
    'depends': ['sale_management', 'purchase'],

    'data': [
        'views/sale_order_line_views.xml',
        'views/purchase_order_line.xml',
        'views/purchase_order_view.xml',
        'views/purchase_report_template.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
            'setu_product_price_history/static/src/js/button_widget.js',
            'setu_product_price_history/static/src/js/button_widget.xml',
            'setu_product_price_history/static/src/css/button_widget.scss',
        ]
    },

    'installable': True,
    'license': 'LGPL-3',
}
