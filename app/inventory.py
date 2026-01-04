{% extends "layout.html" %}
{% block content %}
<div class="container py-4">
    <h2 class="text-white mb-4">Ripoti ya Stoo (Inventory)</h2>
    <div class="table-responsive bg-dark p-3" style="border-radius: 15px;">
        <table class="table table-dark table-striped">
            <thead>
                <tr>
                    <th>Bidhaa</th>
                    <th>Bei ya Kununua</th>
                    <th>Bei ya Kuuza</th>
                    <th>Faida Tarajiwa</th>
                    <th>Stock</th>
                </tr>
            </thead>
            <tbody>
                {% for p in products %}
                <tr>
                    <td>{{ p.name }}</td>
                    <td>Tsh {{ p.buying_price }}</td>
                    <td>Tsh {{ p.selling_price }}</td>
                    <td class="text-success">Tsh {{ p.selling_price - p.buying_price }}</td>
                    <td>{{ p.stock }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

