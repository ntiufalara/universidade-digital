$(function () {
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
});