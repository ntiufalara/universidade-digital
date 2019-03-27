$(function () {
    // Preenche os campos de acordo com a querystring
    var params = getUrlVars();

    // Adicione campos filtráveis e buscáveis nas listas abaixo
    var filter_fields = [
        'campus_id__id',
        'polo_id__id',
        'curso_id__id',
        'ano_pub',
        'tipo_id__id',
        'categoria_cnpq_id__id',
    ];

    filter_fields.forEach(function (item) {
        if (item in params) {
            $('select[name=' + item + ']').val(params[item]);
        }
    });

    // Filtros na lista de publicações
    $('select').change(function (e) {
        var name = $(this).prop('name');
        var value = $(this).val();

        updateQueryStringParam(name, value);
        location.reload();
    });

    var marcado = false;

    // Seleção de busca
    $('#marcar_todos').click(function () {
        // Marca e desmarca ao selecionar todos
        var checks = $('input[type=checkbox]');
        if (marcado === false) {
            checks.prop('checked', true);
            $(this).text('Desmarcar todos');
            marcado = true;
        } else {
            checks.prop('checked', false);
            $(this).text('Marcar todos');
            marcado = false;
        }
    });

    // Valida o formulário antes de enviar
    $('#bt_buscar').click(function (e) {
        var checks = $('input[type=checkbox]');

        var checks_bool = [];

        checks.each(function (index, item) {
            checks_bool.push($(item).prop('checked'));
        });

        // Verifica se existe algum checkbox marcado
        if (!~checks_bool.indexOf(true)) {
            $('#error_msg').removeClass('d-none');
            e.preventDefault();
        }
    });

});