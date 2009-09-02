var ui = {};

ui.showError = function (message) {
    $("#error").show().html(message);
}

ui.onSendClick = function () {
    var user = $('#user').val(),
        title = $('#title').val(),
        message = $('#message').val(),
        notice;

    user = $.trim(user);
    message = $.trim(message);

    if (user === "") {
        ui.showError("empty user");
        return;
    }

    if (title === "") {
        ui.showError("empty title");
        return;
    }

    if (message === "") {
        ui.showError("empty message");
        return;
    }

    notice = model.Notice(null, title, message, user);

    requests.create_notice_json(notice, ui.onSendOK, ui.onSendError);
};

ui.onSendOK = function (notice) {
    ui.addNotice(notice);
};

ui.onSendError = function (response) {
    ui.showError(response.responseText);
};

ui.addNotice = function (notice) {
    var timeline = $('#timeline');

    timeline.prepend(
        h.div({'class': 'notice', 'id': notice.uid},
            h.div({'class': 'notice-title'}, h.em(notice.author), ": ",
                h.a({'href': '/notice/' + notice.uid}, notice.title)),
            h.div({'class': 'notice-body'}, notice.body)).str());
};
