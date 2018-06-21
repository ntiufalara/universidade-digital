$(function () {
    // Adiciona as máscaras de campos
    $('#cpf').mask('999.999.999-99');
    $('#celular').mask('(99) 9 9999-9999');
    $('#outro_telefone').focusout(function () {
        var phone, element;
        element = $(this);
        element.unmask();
        phone = element.val().replace(/\D/g, '');
        if (phone.length > 10) {
            element.mask("(99) 99999-9999");
        } else {
            element.mask("(99) 9999-99999");
        }
    }).trigger('focusout');

    // Quando o campus mudar, atualize a lista de polos
    $('#campus').change(function () {
        $.ajax({
            url: '/ud_monitoria_cadastro/filtrar_local/polo',
            data: {campus_id: $(this).val()},
            method: 'POST',
            success: function (data) {
                var polos = JSON.parse(data);

                var options = '<option></option>';
                for (var i in polos) {
                    options += '<option value="' + polos[i].id + '">' + polos[i].name + '</option>';
                }
                $('#polo').html(options);

            }
        });
    });

    // Quando o polo mudar, atualize a lista de cursos
    $('#polo').change(function () {
        $.ajax({
            url: '/ud_monitoria_cadastro/filtrar_local/curso',
            data: {polo_id: $(this).val()},
            method: 'POST',
            success: function (data) {
                var cursos = JSON.parse(data);

                var options = '<option></option>';
                for (var i in cursos) {
                    options += '<option value="' + cursos[i].id + '">' + cursos[i].name + '</option>';
                }
                $('#curso').html(options);

            }
        });
    });

    $('#sucessoModal').modal('show');

    $('#form_cadastro_aluno').submit(function (event) {
        $('#bt_salvar').attr('disabled', 'true');
        return true;
    })

});