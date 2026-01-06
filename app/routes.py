from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return """
    <html>
    <head>
        <title>Business Systems OP</title>
        <style>
            body{
                font-family: Arial;
                background:#0f172a;
                color:white;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
            }
            .box{
                background:#111827;
                padding:40px;
                border-radius:12px;
                text-align:center;
            }
            a{
                display:block;
                margin-top:15px;
                color:#22c55e;
                text-decoration:none;
                font-weight:bold;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>✅ Mfumo Umeanza Kazi</h1>
            <p>Business Systems Operation</p>
            <a href="/login">Nenda Login</a>
        </div>
    </body>
    </html>
    """
