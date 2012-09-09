function showSelectCategoryInput(event) {
    event.preventDefault();
    document.getElementById('new_category_input').value = '';
    document.getElementById('new_category_input_container').style.setProperty('display', 'none');
    document.getElementById('category_input_container').style.setProperty('display', 'block');
}

function showAddCategoryInput(event) {
    event.preventDefault();
    var newCategoryInputContainer = document.getElementById('new_category_input_container');
    if (!newCategoryInputContainer) {
        newCategoryInputContainer = document.createElement('div');
        newCategoryInputContainer.className = 'input_container';
        newCategoryInputContainer.id = 'new_category_input_container';

        var newCategoryInput = document.createElement('input');
        newCategoryInput.setAttribute('name', 'new_category');
        newCategoryInput.className = 'text_input';
        newCategoryInput.id = 'new_category_input';

        newCategoryInputContainer.appendChild(newCategoryInput);

        var newCategoryLink = document.createElement('a');
        newCategoryLink.className = 'obvious_link inline_button interface_button';
        newCategoryLink.id = 'select_category_button';
        newCategoryLink.setAttribute('href', '#');
        newCategoryLink.textContent = 'x';
        newCategoryLink.addEventListener('click', showSelectCategoryInput);

        newCategoryInputContainer.appendChild(newCategoryLink);

        document.getElementById('category_input_container').parentNode.appendChild(newCategoryInputContainer);
    }

    document.getElementById('category_input').value = '';
    document.getElementById('category_input_container').style.setProperty('display', 'none');
    newCategoryInputContainer.style.setProperty('display', 'block');
}

function deleteArticle(event) {
    event.preventDefault();
    var messageHolder = document.getElementById('message_holder');
    messageHolder.innerHTML = '';
    messageHolder.style.setProperty('display', 'none');
    var request = new XMLHttpRequest();
    request.open('DELETE', '');
    request.addEventListener('readystatechange', function() {
        if (request.readyState === 4) {
            if (request.status === 200) {
                window.location = '/';
            } else {
                messageHolder.style.setProperty('display', 'block');
                var message = document.createElement('div');
                message.className = 'error_message';
                message.textContent = 'Unable to delete';
                messageHolder.appendChild(message);
            }
        }
    });
    request.send();
}

function initialize() {
    var newCategoryButton = document.getElementById('new_category_button');
    if (newCategoryButton) {
        newCategoryButton.addEventListener('click', showAddCategoryInput);
    }
    var deleteButton = document.getElementById('delete_button');
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteArticle);
    }
}

window.addEventListener('load', initialize);
