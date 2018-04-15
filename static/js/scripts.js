 function recalculate() {
    var table = document.getElementById("verbnoun-table");

    var priorities = [];
    var weights = [];
    var cells = [];
    var totalPriority = 0;

    var minRow = 1;
    var maxRow = table.rows.length - 1;
    var minCell = 2;
    var maxCell = table.rows[0].cells.length - 1;

    for (j = 2; j < maxCell; j++) {
      weights.push([]);
    }

    for (i = minRow; i < maxRow; i++) {
      var priority = parseInt(table.rows[i].cells[1].children[0].value);
      priorities.push(priority);
      totalPriority += priority;
      for (j = minCell; j < maxCell; j++) {
        var weight = parseInt(table.rows[i].cells[j].children[0].value);
        weights[j - minCell].push(weight);
      }
    }

    table.rows[maxRow].cells[1].innerHTML = totalPriority;

    for (j = minCell; j < maxCell; j++) {
      var totalWeight = 0;
      for (i = minRow; i < maxRow; i++) {
        totalWeight += priorities[i - minRow] * weights[j - minCell][i - minRow] * 0.5;
      }
      table.rows[maxRow].cells[j].innerHTML = totalWeight;
    }
  }

  function prepare() {
    var table = document.getElementById("verbnoun-table");

    var cells = [];

    var minRow = 1;
    var maxRow = table.rows.length - 1;
    var minCell = 2;
    var maxCell = table.rows[0].cells.length - 1;

    for (i = 0; i < table.rows.length; i++) {
      cells[i] = [];
      cells[i].push(table.rows[i].cells[0].innerHTML);
    }

    cells[0].push(table.rows[0].cells[1].innerHTML);

    for (i = minRow; i < maxRow; i++) {
      cells[i].push(table.rows[i].cells[1].children[0].value);
    }

    cells[maxRow].push(table.rows[maxRow].cells[1].innerHTML);

    for (j = minCell; j < maxCell; j++) {
      cells[0].push(table.rows[0].cells[j].innerHTML);
      for (i = minRow; i < maxRow; i++) {
        cells[i].push(table.rows[i].cells[j].children[0].value);
      }
      cells[maxRow].push(table.rows[maxRow].cells[j].innerHTML);
    }

    var cellsJSON = JSON.stringify(cells).replace(/'/g, '"');
    return cellsJSON;
  }

  function save_article() {
    body = prepare();
    window.location = "save_article/" + body;
  }

  /*function update_article() {
    body = prepare();
    window.location = "/update_article/" + {{ article.id }} +'/'+ body;
  }*/

  function load_article() {
    document.getElementById("vntitle").innerHTML = "VerbNoun " + '{{ article.create_date }}';
    var cells = JSON.parse('{{ article.body | safe }}');
    console.log(cells);
    var table = document.getElementById("verbnoun-table");
    var minRow = 1;
    var maxRow = cells.length - 1;
    var minCell = 2;
    var maxCell = cells[0].length;
    var priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have'];
    var weights = ['No', 'Partial', 'Yes'];

    var tbody = table.createTBody();
    var row = tbody.insertRow();

    var emptyheader = document.createElement("TH");
    for (j = 0; j < 3; j++) {
      data = cells[0][j];
      emptyheader.innerHTML = data;
    }
    row.appendChild(emptyheader);
    emptyheader.setAttribute("colspan", 3);

    for (j = 3; j < maxCell; j++) {
      data = cells[0][j];
      header = document.createElement("TH");
      header.innerHTML = data;
      row.appendChild(header);
      if (data != "") {
        header.setAttribute("colspan", cells[0][j+1]);
        header.setAttribute("class", "text-center");
        j++;
      }
    }

    var h2 = tbody.insertRow();
    for (j = 0; j < cells[1].length; j++) {
      data = cells[1][j];
      header = document.createElement("TH");
      header.innerHTML = data;
      h2.appendChild(header);
    }

    for (i = 2; i < cells.length-1; i++) {
      rnumber = cells[i][0];
      row = tbody.insertRow();
      cell0 = row.insertCell();
      cell0.innerHTML = '<b>' + rnumber + '</b>';

      rname = cells[i][1];
      cell1 = row.insertCell();
      cell1.innerHTML = rname;

      rpriority = priorities[Number.parseInt(cells[i][2])];
      cell2 = row.insertCell();
      cell2.innerHTML = '<b>' + rpriority + '</b>';

      for (j=3; j < cells[i].length; j++) {
        data = weights[Number.parseInt(cells[i][j])];
        cell = row.insertCell();
        cell.innerHTML = data;
      }

    }

    totalrow = tbody.insertRow();
    totalcell = totalrow.insertCell();
    totalrow.setAttribute("id", "totalrow");
    totalcell.setAttribute("colspan", 2);
    totalcell.setAttribute("class", "text-center");
    totalcell.innerHTML = "<b>Total: </b>";

    console.log(cells[cells.length-1]);

    for (k = 2; k < cells[cells.length-1].length; k++) {
      cell = totalrow.insertCell();
      cell.setAttribute("class", "text-center");
      cell.innerHTML = '<b>' + cells[cells.length-1][k] + '</b>';
    }
  }

  function edit_article() {
    var cells = JSON.parse('{{ article.body | safe }}');
    var table = document.getElementById("verbnoun-table");
    var minRow = 1;
    var maxRow = cells.length - 1;
    var minCell = 2;
    var maxCell = cells[0].length;
    var priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have'];
    var weights = ['No', 'Partial', 'Yes'];

    var tbody = table.createTBody();
    var row = tbody.insertRow();
    for (j = 0; j < maxCell; j++) {
      data = cells[0][j];
      header = document.createElement("TH");
      row.appendChild(header)
      header.innerHTML = data;
    }
    row.insertCell();

    for (i = minRow; i < maxRow; i++) {
      data = cells[i][0];
      row = tbody.insertRow();
      cell = row.insertCell();
      cell.innerHTML = data;
      data = priorities[cells[i][1]];
      cell = row.insertCell();
      select = document.createElement("SELECT");
      select.className = 'form-control';
      for (k = 1; k < priorities.length; k++) {
        var option = document.createElement("OPTION");
        option.value = k;
        option.text = priorities[k];
        select.add(option);
      }
      select.value = cells[i][1];
      select.onchange = function(){recalculate()};
      cell.appendChild(select);
      for (j = minCell; j < maxCell; j++) {
        data = weights[cells[i][j]];
        cell = row.insertCell();
        select = document.createElement("SELECT");
        select.className = 'form-control';
        for (k = 0; k < weights.length; k++) {
          var option = document.createElement("OPTION");
          option.value = k;
          option.text = weights[k];
          select.add(option);
        }
        select.value = cells[i][j];
        select.onchange = function(){recalculate()};
        cell.appendChild(select);
      }
      cell = row.insertCell();
      delete_button = document.createElement("A");
      delete_button.className = 'btn btn-danger';
      delete_button.text = 'Delete';
      delete_button.href = '/article_edit_delete_requirement/' + cells[i][0];
      cell.appendChild(delete_button);
    }

    row = tbody.insertRow();
    cell = row.insertCell();
    cell.innerHTML = 'Total:';
    for (j = 1; j < maxCell; j++) {
      cell = row.insertCell();
    }
    row.insertCell();
    recalculate();
  }

  function close_article() {
    window.location = "/dashboard"
  }

  var components_dictionary = JSON.parse('{{ components_list | safe }}');
  var selectedComponents = [];

  function fillBySaved(project_components) {
    var components_selected_select = document.getElementById("components_selected");
    var components_selected = [];
    for (i = 0; i < project_components.length; i++) {
      var option = document.createElement("OPTION");
      option.text = project_components[i][0] + ":";
      components_selected_select.add(option);
      for (j = 1; j < project_components[i].length; j++) {
          var option = document.createElement("OPTION");
          option.text = "- " + project_components[i][j];
          components_selected_select.add(option);

          for (k = 0; k < components_dictionary.length; k++) {
            if (components_dictionary[k]['name'] == project_components[i][j] && components_dictionary[k]['category'] == project_components[i][0]) {
              var obj = {
                "group": components_dictionary[k]['gname'],
                "category": components_dictionary[k]['category'],
                "name": components_dictionary[k]['name'],
                "id": components_dictionary[k]['id'],
                "link": components_dictionary[k]['link']
              };
              selectedComponents.push(obj);
          }
        }
      }
    }
    console.log(selectedComponents);
  }

  function add_article_wizard_2_onload() {
    var project_components = null;
    try {
      project_components = JSON.parse('{{ project_components | safe }}');
    } catch (err) {}
    if (project_components != null) {
      fillBySaved(project_components);
    }

    var groups_selector = document.getElementById("groups");
    var groups = [];
    var categories = [];
    var names = [];
    for (i = 0; i < components_dictionary.length; i++) {
      group = components_dictionary[i]['gname'];
      category = components_dictionary[i]['category'];
      name = components_dictionary[i]['name'];
      if (groups.includes(group) == false) { groups.push(group) }
      if (categories.includes(category) == false) { categories.push(category) }
      if (names.includes(name) == false) { names.push(name) }
    }

    for (i = 0; i < groups.length; i++) {
      var option = document.createElement("OPTION");
      option.value = i;
      option.text = groups[i];
      groups_selector.add(option);
    }
  }

  function add_article_wizard_2_groups() {
    var groups_select = document.getElementById("groups");
    var categories_select = document.getElementById("categories");
    var groups_options = groups_select && groups_select.options;
    var selected_groups = [];
    var categories = [];

    for (i = 0; i < groups_options.length; i++) {
      if (groups_options[i].selected) {
        selected_groups.push(groups_options[i].text);
      }
    }

    for (i = 0; i < components_dictionary.length; i++) {
      if (selected_groups.includes(components_dictionary[i].gname)) {
        if (categories.includes(components_dictionary[i].category)  == false) {
          categories.push(components_dictionary[i].category);
        }
      }
    }
    categories_select_length = categories_select.children.length;
    for (i = 0; i < categories_select_length; i++) {
      categories_select.remove(categories_select.children[i]);
    }

    for (i = 0; i < categories.length; i++) {
      var option = document.createElement("OPTION");
      option.value = i;
      option.text = categories[i];
      categories_select.add(option);
    }
  }

  function add_article_wizard_2_categories() {
    var categories_select = document.getElementById("categories");
    var components_select = document.getElementById("components");
    var categories_options = categories_select && categories_select.options;
    var selected_categories = [];
    var components = [];

    for (i = 0; i < categories_options.length; i++) {
      if (categories_options[i].selected) {
        selected_categories.push(categories_options[i].text);
      }
    }

    for (i = 0; i < components_dictionary.length; i++) {
      if (selected_categories.includes(components_dictionary[i].category)) {
        components.push(components_dictionary[i]);
      }
    }

    components_select_length = components_select.children.length;
    for (i = 0; i < components_select_length; i++) {
      components_select.remove(components_select.children[i]);
    }

    for (i = 0; i < selected_categories.length; i++) {
      var option = document.createElement("OPTION");
      option.text = selected_categories[i] + ":";
      components_select.add(option);
      for (j = 0; j < components.length; j++) {
        if (components[j].category == selected_categories[i]) {
          var option = document.createElement("OPTION");
          option.text = "- " + components[j].name;
          components_select.add(option);
        }
      }
    }
  }

  function add_article_wizard_2_add() {
    var components_select = document.getElementById("components");
    var components_selected_select = document.getElementById("components_selected");
    var components_options = components_select && components_select.options;
    var components_selected_options = components_selected_select && components_selected_select.options;
    var categories = [];
    var components_selected = [];

    for (i = 0; i < components_options.length; i++) {
      if (components_options[i].text.endsWith(":")) {
        var category = components_options[i].text.replace(/:$/, "");
      }
      if (components_options[i].selected) {
        for (j = 0; j < components_dictionary.length; j++) {
          if (components_dictionary[j].category == category) {
            var name = components_options[i].text.replace(/^- /, "");
            if (components_dictionary[j].name == name) {
              if (categories.includes(category) == false) {
                categories.push(category);
              }
              components_selected.push(components_dictionary[j]);
            }
          }
        }
      }
    }

    for (i = 0; i < components_selected_options.length; i++) {
      if (components_selected_options[i].text.endsWith(":")) {
        var category = components_selected_options[i].text.replace(/:$/, "");
        if (categories.includes(category) == false) {
          categories.push(category);
        }
      } else {
        var name = components_selected_options[i].text.replace(/^- /, "");
        for (j = 0; j < components_dictionary.length; j++) {
          if (components_dictionary[j].category == category) {
            if (components_dictionary[j].name == name) {
              components_selected.push(components_dictionary[j]);
            }
          }
        }
      }
    }

    components_selected_select_length = components_selected_select.children.length;
    for (i = 0; i < components_selected_select_length; i++) {
      components_selected_select.remove(components_selected_select.children[i]);
    }

    for (i = 0; i < categories.length; i++) {
      var option = document.createElement("OPTION");
      option.text = categories[i] + ":";
      components_selected_select.add(option);
      for (j = 0; j < components_selected.length; j++) {
        if (components_selected[j].category == categories[i]) {
          var option = document.createElement("OPTION");
          option.text = "- " + components_selected[j].name;
          components_selected_select.add(option);
        }
      }
    }
    selectedComponents = components_selected;
  }

  function add_article_wizard_2_remove() {
    var components_selected_select = document.getElementById("components_selected");
    var components_selected_options = components_selected_select && components_selected_select.options;
    var components_selected = [];
    var categories = [];

    for (i = 0; i < components_selected_options.length; i++) {
      if (components_selected_options[i].selected == false) {
        if (components_selected_options[i].text.endsWith(":")) {
          var category = components_selected_options[i].text.replace(/:$/, "");
          if (categories.includes(category) == false) {
            categories.push(category);
          }
        } else {
          for (j = 0; j < components_dictionary.length; j++) {
            var component = components_dictionary[j];
            var name = components_selected_options[i].text.replace(/^- /, "");
            if (component.category == category && component.name == name) {
              components_selected.push(component);
            }
          }
        }
      }
      selectedComponents = components_selected;
    }

    components_selected_select_length = components_selected_select.children.length;
    for (i = 0; i < components_selected_select_length; i++) {
      components_selected_select.remove(components_selected_select.children[i]);
    }

    for (i = 0; i < categories.length; i++) {
      for (j = 0; j < components_selected.length; j++) {
        if (components_selected[j].category == categories[i]) {
          var option = document.createElement("OPTION");
          option.text = categories[i] + ":";
          components_selected_select.add(option);
          break;
        }
      }
      for (j = 0; j < components_selected.length; j++) {
        if (components_selected[j].category == categories[i]) {
          option = document.createElement("OPTION");
          option.text = "- " + components_selected[j].name;
          components_selected_select.add(option);
        }
      }
    }
  }

  function submitComponents() {
    console.log("redirect");
    var submitObj = [];
    var processedCategories = [];
    for (i = 0; i < selectedComponents.length; i++) {
      var arr = [];
      if (processedCategories.indexOf(selectedComponents[i].category) == -1) {
        processedCategories.push(selectedComponents[i].category);
        arr.push(selectedComponents[i].category);
        for (j = 0; j < selectedComponents.length; j++) {
          if (selectedComponents[j].category == arr[0]) {
            arr.push(selectedComponents[j].name);
          }
        }
        submitObj.push(arr);
      }
    }
    var body = JSON.stringify(submitObj);
    console.log(body);

    $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
    $.ajax({
      type: "POST",
        headers: {"Content-Type": "application/json"},
          url: $SCRIPT_ROOT + "/article_add_wizard_2",
          data: body,
          success: function(response) {
              //console.log(response);
              window.location = "article_add_wizard_3";
            },
            error: function(response, error) {
                console.log(response);
                console.log(error);
              }
          });
    return false;
  }

  function tableLoad() {
    var table = document.getElementById("verbnoun-table");

    var components = JSON.parse('{{ componentsJSON | safe }}');
    var requirements = JSON.parse('{{ requirementsJSON | safe }}');
    console.log(components);
    console.log(requirements);
    var priorities = ['', 'Nice to have', 'Whish list', 'Based on Policy', 'Best Practice', 'Must have'];
    var weights = ['No', 'Partial', 'Yes'];

    // Row 1
    var row = table.insertRow();
    var header = document.createElement("TH");
    row.appendChild(header);

    header = document.createElement("TH");
    row.appendChild(header);

    header = document.createElement("TH");
    row.appendChild(header);

    for (i = 0; i < components.length; i++) {
      header = document.createElement("TH");
      // header.innerHTML = components[i][0];
      header.colSpan = components[i].length - 1;
      var paragraph = document.createElement("P");
      paragraph.className = 'text-center';
      paragraph.innerHTML = components[i][0];
      header.appendChild(paragraph);
      row.appendChild(header);
    }

    // Row 2
    row = table.insertRow();
    var header = document.createElement("TH");
    header.innerHTML = "R#";
    row.appendChild(header);

    header = document.createElement("TH");
    header.innerHTML = "Requirement";
    row.appendChild(header);

    header = document.createElement("TH");
    header.innerHTML = "Priority";
    row.appendChild(header);

    for (i = 0; i < components.length; i++) {
      for (j = 1; j < components[i].length; j++) {
        header = document.createElement("TH");
        header.innerHTML = components[i][j];
        row.appendChild(header);
      }
    }

    // Requirements
    for (i = 0; i < requirements.length; i++) {
      var requirement_number = 0;
      for (j = 1; j < requirements[i].length; j++) {
        requirement_number++;
        var label = "";
        if (requirements[i][0] == 'Business requirements') { label = "BR"; }
        if (requirements[i][0] == 'Technical requirements') { label = "TR"; }
        if (requirements[i][0] == 'Governance requirements') { label = "GR"; }
        row = table.insertRow();
        var cell = row.insertCell();
        cell.innerHTML = '<b>' + label + requirement_number.toString() + '</b>';
        cell = row.insertCell();
        cell.innerHTML = requirements[i][j];

        // Priorities selector
        var cell = row.insertCell();
        select = document.createElement("SELECT");
        select.className = 'form-control';
        select.onchange = function(){tableRecalculate()};
        for (k = 1; k < priorities.length; k++) {
          var option = document.createElement("OPTION");
          option.value = k;
          option.text = priorities[k];
          select.add(option);
        }
        cell.appendChild(select);

        //Weight selector
        for (k = 0; k < components.length; k++) {
          for (l = 1; l < components[k].length; l++) {
            cell = row.insertCell();
            select = document.createElement("SELECT");
            select.className = 'form-control';
            select.onchange = function(){tableRecalculate()};
            for (m = 0; m < weights.length; m++) {
              var option = document.createElement("OPTION");
              option.value = m;
              option.text = weights[m];
              select.add(option);
            }
            cell.appendChild(select);
          }
        }


      }
    }

    // Last row
    row = table.insertRow();
    row.setAttribute("id", "totalRow");
    cell = row.insertCell();
    cell = row.insertCell();
    cell.innerHTML = 'Total:';

    for (i = 2; i < table.rows[2].cells.length; i++) {
      cell = row.insertCell();
    }
    tableRecalculate();
  }

  function tableRecalculate() {
    var table = document.getElementById("verbnoun-table");
    var total_priority = 0;
    var total_weights = [];
    var row = table.rows[table.rows.length - 1];

    for (i = 2; i < table.rows.length - 1; i++) {
      total_priority += parseInt(table.rows[i].cells[2].children[0].value);
    }

    row.cells[2].innerHTML = total_priority.toString();

    for (i = 0; i < table.rows[2].cells.length; i++) {
      total_weights.push(0);
    }

    for (i = 2; i < table.rows.length - 1; i++) {
      for (j = 3; j < table.rows[2].cells.length; j++) {
        priority = parseInt(table.rows[i].cells[2].children[0].value);
        weight = parseInt(table.rows[i].cells[j].children[0].value);
        total_weights[j] += priority * weight * .5
      }
    }

    for (i = 3; i < table.rows[2].cells.length; i++) {
      row.cells[i].innerHTML = total_weights[i].toString();
    }
  }

  function add_article_wizard_6_save() {
    var table = document.getElementById("verbnoun-table");
    var cells = [];

    for (i = 0; i < table.rows.length; i++) {
      var row = table.rows[i];
      cells.push([]);
      for (j = 0; j < row.cells.length; j++) {
        var cell = row.cells[j];
        if (i == 0) {
          if (j < 3) {
            cells[i].push("");
          } else {
            cells[i].push(cell.children[0].innerHTML);
            cells[i].push(cell.colSpan);
          }
        } else if (i == 1) {
          cells[i].push(cell.innerHTML);
        } else if (i < table.rows.length - 1) {
          if (j < 2) {
            cells[i].push(cell.innerHTML);
          } else {
            cells[i].push(cell.children[0].value);
          }
        } else {
            cells[i].push(cell.innerHTML);
        }
      }
    }

    var body = JSON.stringify(cells);
    $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
    $.ajax({
      type: "POST",
        headers: {"Content-Type": "application/json"},
          url: $SCRIPT_ROOT + "/article_add_wizard_6",
          data: body,
          success: function(response) {
              //console.log(response);
              window.location = "newarticle";
            },
            error: function(response, error) {
                console.log(response);
                console.log(error);
              }
          });
    return false;

  }