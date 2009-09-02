var h = {};

h.tag = function (name) {
    var tag = name, attrs={}, childs=[];

    if(arguments.length > 0) {
        if (typeof(arguments[1]) === 'object' &&
                typeof(arguments[1].str) === 'undefined') {
            attrs = arguments[1];
            childs = Array.prototype.slice.call(arguments, 2);
        }
        else {
            childs = Array.prototype.slice.call(arguments, 1);
        }
    }

    return {'tag': name, 'attrs': attrs, 'childs': childs,
       'str': function () {
            var i, childsStr = [], attrsStr = [], attrStr, all;

            for(i = 0; i < childs.length; i += 1) {
               if(typeof(childs[i].str) !== 'undefined') {
                   childsStr.push(childs[i].str());
               }
               else {
                   childsStr.push(childs[i]);
               }
            }

            for(i in attrs) {
               attrsStr.push(' ' + i + '="' + attrs[i] + '"');
            }

            attrStr = attrsStr.join('');
            all = ['<', name, attrStr, '>'].concat(childsStr, ['</', name, '>']);
            return all.join('');
        },
        'add': function (child) {
            childs.push(child);
        }
    };
};

h.newTag = function (name) {
    return function() {
        Array.prototype.unshift.call(arguments, name);
        return h.tag.apply(h.tag, arguments);
    }
};

h.TAGS = ['a', 'div', 'span', 'ul', 'li', 'ol', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'p', 'head', 'body', 'iframe', 'button', 'input',
    'textarea', 'img', 'link', 'script', 'table', 'tr', 'td', 'th',
    'tbody', 'thead', 'title', 'html', 'center', 'b', 'em', 'strong',
    'u', 'i'];

for(i in h.TAGS) {
    tag = h.TAGS[i];
    h[tag] = h.newTag(tag);
}
