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

function initialize() {
    document.getElementById('new_category_button').addEventListener('click', showAddCategoryInput);
}

window.addEventListener('load', initialize);
