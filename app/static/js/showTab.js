function showTab(tabName) {
    let contents = document.querySelectorAll('.profile_tab-content');
    let buttons = document.querySelectorAll('.profile_tab-button');

    contents.forEach(content => {
        content.classList.remove('active');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
    });

    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}