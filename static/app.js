const cards=[...document.querySelectorAll('.deal')];
const search=document.querySelector('#search'), category=document.querySelector('#category'),
 retailer=document.querySelector('#retailer'), minimum=document.querySelector('#minimum'), sort=document.querySelector('#sort');
function fillSelect(el, attr){const values=[...new Set(cards.map(c=>c.dataset[attr]).filter(Boolean))].sort();values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v.replace(/\b\w/g,x=>x.toUpperCase());el.append(o)})}
fillSelect(category,'category');fillSelect(retailer,'retailer');
function update(){
 const q=search.value.toLowerCase(), cat=category.value, ret=retailer.value, min=Number(minimum.value);
 const visible=cards.filter(c=>(c.dataset.title.includes(q))&&(!cat||c.dataset.category===cat)&&(!ret||c.dataset.retailer===ret)&&Number(c.dataset.discount)>=min);
 visible.sort((a,b)=>{const k=sort.value;if(k==='savings')return Number(b.dataset.savings)-Number(a.dataset.savings);if(k==='price')return Number(a.dataset.price)-Number(b.dataset.price);if(k==='az')return a.dataset.title.localeCompare(b.dataset.title);return Number(b.dataset.discount)-Number(a.dataset.discount)||Number(a.dataset.price)-Number(b.dataset.price)});
 cards.forEach(c=>c.hidden=true);visible.forEach((c,i)=>{c.hidden=false;c.querySelector('.rank').textContent='#'+(i+1);document.querySelector('#listing').append(c)});
}
[search,category,retailer,minimum,sort].forEach(el=>el.addEventListener('input',update));
