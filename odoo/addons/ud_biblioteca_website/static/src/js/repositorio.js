$(function () {
    // Preenche os campos de acordo com a querystring
    var params = getUrlVars();

    // Filtros de busca
    var q_filter = [];

    // Adicione campos filtráveis e buscáveis nas listas abaixo
    var filter_fields = [
        'campus_id__id',
        'polo_id__id',
        'curso_id__id',
        'ano_pub',
        'tipo_id__id',
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

        // Berifica se existe algum checkbox marcado
        if (!~checks_bool.indexOf(true)) {
            $('#error_msg').removeClass('d-none');
            e.preventDefault();
        }
    });

    // Seleciona todos na busca por padrão
    // $('input[type=checkbox][name="todos"]').prop('checked', true).trigger('change');

    // Buscar
    // $('#bt_buscar').click(function () {
    //     // obriga o usuário a selecionar um checkbox
    //     if (q_filter.length < 1) {
    //         $('#q').addClass('is-invalid');
    //         $('#erro_msg').removeClass('d-none');
    //     } else {
    //         // remove o erro
    //         $('#q').removeClass('is-invalid');
    //         $('#erro_msg').addClass('d-none');
    //
    //         // executa a busca
    //         for (var i in q_filter) {
    //             updateQueryStringParam(q_filter[i], $('#q').val());
    //         }
    //         updateQueryStringParam('q', $('#q').val());
    //         location.reload();
    //     }
    // });

    // function limparBusca () {
    //     for (var i in q_filter) {
    //         updateQueryStringParam(q_filter[i], '');
    //     }
    //     updateQueryStringParam('q', '');
    // }

    // Campo de busca
    // if ('q' in params) {
    //     $('input[name=q]').val(decodeURIComponent(params.q).replace('+', ' '));
    //     if (params.length === 1) $('#bt_buscar').click();
    // }

});