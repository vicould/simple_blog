String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

function sendCategory(event, categoryInput) {
    event.preventDefault();
    var categoryName = categoryInput.value;
    if (categoryName !== '') {
        var request = new XMLHttpRequest();
        request.addEventListener('readystatechange', function(event) {
            if (request.readyState === 4) {
                if (request.status === 200) {
                    var title = categoryInput.parentNode.parentNode.getElementsByTagName('h2')[0];
                    title.style.setProperty('display', 'block');
                    title.id = categoryName;
                    title.getElementsByTagName('span')[0].textContent = categoryName;
                    categoryInput.parentNode.parentNode.removeChild(categoryInput.parentNode);
                    var newLocationMessageHolder = document.getElementById('new_location');
                    if (!newLocationMessageHolder) {
                        newLocationMessageHolder = document.createElement('div');
                        newLocationMessageHolder.id = 'new_location';
                        var innerContent = document.getElementById('inner_content');
                        innerContent.insertBefore(newLocationMessageHolder, innerContent.firstChild);
                    }
                    newLocationMessageHolder.innerHTML = '';

                    var message = document.createElement('span');
                    message.textContent = 'The page changed. You should go ';
                    newLocationMessageHolder.appendChild(message);

                    var link = document.createElement('a');
                    if (document.URL.toString().endsWith('categories/')) {
                        // only reloads the page if we are listing all the categories
                        link.setAttribute('href', '');
                    } else {
                        // points to the new location of the category otherwise
                        link.setAttribute('href', JSON.parse(request.responseText).new_location);
                    }

                    link.textContent = 'here';
                    newLocationMessageHolder.appendChild(link);
                } else {
                    var oldMessages = categoryInput.parentNode.getElementsByClassName('error_message');
                    for (var i = 0; i < oldMessages.length; i++) {
                        categoryInput.parentNode.removeChild(oldMessages[i]);
                    }
                    var errorContainer = document.createElement('span');
                    errorContainer.className = 'error_message';
                    if (request.status === 409) {
                        errorContainer.textContent = 'Name already taken';
                    } else if (request.status === 400) {
                        errorContainer.textContent = 'Please fill the name';
                    } else {
                        errorContainer.textContent = 'Unexpected error';
                    }
                    categoryInput.parentNode.appendChild(errorContainer);
                }
            }
        });
        request.open('POST', '/categories/' + categoryInput.getAttribute('value') + '/edit/');
        request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        request.send('name=' + encodeURIComponent(categoryName));
    }
}

function showCategoryEditor(event) {
    event.preventDefault();
    var titleContainer = event.target.parentNode;
    var categoryName = titleContainer.id;
    titleContainer.style.setProperty('display', 'none');

    var inputContainer = document.createElement('div');
    inputContainer.className = 'inline_input_container';

    var categoryNameInput = document.createElement('input');
    categoryNameInput.setAttribute('name', 'category');
    categoryNameInput.setAttribute('class', 'input_element text_input');
    categoryNameInput.setAttribute('value', categoryName);
    inputContainer.appendChild(categoryNameInput);

    var submitButton = document.createElement('a');
    submitButton.className = 'form_button inline_button';
    submitButton.setAttribute('href', '#');
    submitButton.addEventListener('click', function(event) {
        event.preventDefault();
        sendCategory(event, categoryNameInput);
    });
    submitButton.textContent = 'Save';
    inputContainer.appendChild(submitButton);

    var hideButton = document.createElement('a');
    hideButton.className = 'hidden_link inline_button';
    hideButton.setAttribute('href', '#');
    hideButton.addEventListener('click', function(event) {
        event.preventDefault();
        titleContainer.parentNode.removeChild(inputContainer);
        titleContainer.style.setProperty('display', 'block');
    });
    hideButton.textContent = 'Cancel';
    inputContainer.appendChild(hideButton);

    titleContainer.parentNode.appendChild(inputContainer);
}

function initialize() {
    var categoryEditors = document.getElementsByClassName('category_edition');
    for (var i = 0; i < categoryEditors.length; i++) {
        categoryEditors[i].addEventListener('click', showCategoryEditor);
    }
}

window.addEventListener('load', initialize);
