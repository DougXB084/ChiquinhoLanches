from django.db import migrations


def criar_historico_dos_pedidos_existentes(apps, schema_editor):
    """Pedidos criados antes do histórico ganham uma entrada com o status atual."""
    Pedido = apps.get_model("core", "Pedido")
    HistoricoStatus = apps.get_model("core", "HistoricoStatus")
    for pedido in Pedido.objects.filter(historico__isnull=True):
        entrada = HistoricoStatus.objects.create(pedido=pedido, status=pedido.status)
        HistoricoStatus.objects.filter(pk=entrada.pk).update(data=pedido.data)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_ingrediente_alter_categoria_options_and_more"),
    ]

    operations = [
        migrations.RunPython(
            criar_historico_dos_pedidos_existentes, migrations.RunPython.noop
        ),
    ]
