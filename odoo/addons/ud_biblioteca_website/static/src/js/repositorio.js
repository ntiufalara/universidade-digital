$(function () {
    // Explicitly save/update a url parameter using HTML5's replaceState().
    function updateQueryStringParam(param, value) {
        var baseUrl = [location.protocol, '//', location.host, location.pathname].join('');
        var urlQueryString = document.location.search;
        var newParam = param + '=' + value,
            params = '?' + newParam;

        // If the "search" string exists, then build params from it
        if (urlQueryString) {
            var keyRegex = new RegExp('([\?&])' + param + '[^&]*');
            // If param exists already, update it
            if (urlQueryString.match(keyRegex) !== null) {
                params = urlQueryString.replace(keyRegex, "$1" + newParam);
            } else { // Otherwise, add it to end of query string
                params = urlQueryString + '&' + newParam;
            }
        }
        window.history.replaceState({}, "", baseUrl + params);
    }

    // Read a page's GET URL variables and return them as an associative array.
    function getUrlVars() {
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for (var i = 0; i < hashes.length; i++) {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    }

    // Filtros na lista de publicações - CURSO
    $('.filtrar-curso').change(function (e) {
        var curso_id = $(this).val();

        updateQueryStringParam('curso_id', curso_id);
        location.reload();
    });

    // Filtros na lista de publicações - ANO
    $('.filtrar-ano').change(function () {
        var ano = $(this).val();

        updateQueryStringParam('ano', ano);
        location.reload();
    });

    // Avança ou volta na paginação
    $('#prev_page').click(function () {
        var prev = $(this).attr('data-prev');

        updateQueryStringParam('page_num', prev);
        location.reload();
    });
    $('#next_page').click(function () {
        var next = $(this).attr('data-next');

        updateQueryStringParam('page_num', next);
        location.reload();
    });

    // Preenche os campos de acordo com a querystring
    var params = getUrlVars();
    if ('q' in params) {
        $('#buscar').val(decodeURIComponent(params.q));
    }
    if ('curso_id' in params) {
        $('#filtrar-curso').val(params.curso_id);
    }
    if ('ano' in params) {
        $('#filtrar-ano').val(params.ano);
    }
});