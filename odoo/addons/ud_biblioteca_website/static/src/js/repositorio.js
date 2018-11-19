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
        'ano',
        'tipo_id__id',
    ];
    // Campo de busca
    if ('q' in params) {
        $('input[name=q]').val(decodeURIComponent(params.q));
    }

    filter_fields.forEach(function (item) {
        if (item in params) {
            $('select[name=' + item + ']').val(params[item]);
        }
    });

    // Seleção de busca
    $('input[type=checkbox]').change(function () {
        var name = $(this).attr('name');
        var checked = $(this).is(':checked');

        // Marca e desmarca ao selecionar todos
        var checks = $('input[type=checkbox]:not(input[name="todos"])');
        if (name === 'todos' && checked === true) {
            checks.prop('checked', true);
            checks.prop('disabled', true);
        } else if (name === 'todos' && checked === false) {
            checks.prop('checked', false);
            checks.prop('disabled', false);
        }

        checks.each(function (i) {
            var c_name = $(checks[i]).attr('name');
            var c_value = $(checks[i]).prop('checked');

            // Adiciona ou remove a seleção da lista de filtros
            if (c_value && !q_filter.includes(c_name)) {
                q_filter.push(c_name);
            } else if (!c_value && q_filter.includes(c_name)) {
                q_filter.splice(
                    q_filter.indexOf(c_name), 1
                );
            }
        });

    });

    // Seleciona todos na busca por padrão
    $('input[type=checkbox][name="todos"]').prop('checked', true).trigger('change');

    // Filtros na lista de publicações
    $('select').change(function (e) {
        var name = $(this).prop('name');
        var value = $(this).val();

        updateQueryStringParam(name, value);
        location.reload();
    });

    // Buscar
    $('#bt_buscar').click(function () {
        // obriga o usuário a selecionar um checkbox
        if (q_filter.length < 1) {
            $('#q').addClass('is-invalid');
            $('#erro_msg').removeClass('d-none');
        } else {
            // remove o erro
            $('#q').removeClass('is-invalid');
            $('#erro_msg').addClass('d-none');

            // executa a busca
            for (var i in q_filter) {
                updateQueryStringParam(q_filter[i], $('#q').val());
            }
            updateQueryStringParam('q', $('#q').val());
            location.reload();
        }
    });

    $('#limpar_busca').click(function () {
        for (var i in q_filter) {
            updateQueryStringParam(q_filter[i], '');
        }
        updateQueryStringParam('q', '');
        location.reload();
    });
});