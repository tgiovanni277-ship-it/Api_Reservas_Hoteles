
const API_BASE_URL=(import.meta.env.VITE_API_BASE_URL||"").replace(/\/+$/,"");
const reservations=[];
let token=null;
let visibleMonth=startOfMonth(new Date());
let selectedDate=dateKey(new Date());
const monthLabel=document.querySelector("#month-label");
const calendarDays=document.querySelector("#calendar-days");
const agenda=document.querySelector("#agenda");
const message=document.querySelector("#message");
const apiState=document.querySelector("#api-state");
const bookingDialog=document.querySelector("#booking-dialog");
const loginDialog=document.querySelector("#login-dialog");
const reservationForm=document.querySelector("#reservation-form");
function startOfMonth(date){return new Date(date.getFullYear(),date.getMonth(),1)}
function dateKey(date){return [date.getFullYear(),String(date.getMonth()+1).padStart(2,"0"),String(date.getDate()).padStart(2,"0")].join("-")}
function parseDate(value){const parts=value.split("-").map(Number);return new Date(parts[0],parts[1]-1,parts[2])}
function addDays(value,days){const date=parseDate(value);date.setDate(date.getDate()+days);return dateKey(date)}
function active(item){return item.estado!=="cancelada"}
function overlapsDay(item,day){return item.fecha_entrada<=day&&day<item.fecha_salida&&active(item)}
function monthReservations(date){const first=dateKey(startOfMonth(date));const next=dateKey(new Date(date.getFullYear(),date.getMonth()+1,1));return reservations.filter((item)=>active(item)&&item.fecha_entrada<next&&item.fecha_salida>first)}
function formatLongDate(value){return new Intl.DateTimeFormat("es-CO",{weekday:"long",day:"numeric",month:"long",year:"numeric"}).format(parseDate(value))}
function formatShortDate(value){return new Intl.DateTimeFormat("es-CO",{day:"numeric",month:"short"}).format(parseDate(value))}
function setMessage(text,kind){message.textContent=text||"";message.dataset.kind=kind||""}
function updateApiState(state,label){apiState.dataset.state=state;document.querySelector("#api-state-label").textContent=label}
function make(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined)node.textContent=text;return node}
function renderCalendar(){
  const name=new Intl.DateTimeFormat("es-CO",{month:"long",year:"numeric"}).format(visibleMonth);
  monthLabel.textContent=name.charAt(0).toLocaleUpperCase("es-CO")+name.slice(1);
  calendarDays.replaceChildren();
  const first=startOfMonth(visibleMonth);const offset=(first.getDay()+6)%7;const gridStart=new Date(first);gridStart.setDate(first.getDate()-offset);const today=dateKey(new Date());
  for(let index=0;index<42;index+=1){
    const date=new Date(gridStart);date.setDate(gridStart.getDate()+index);const key=dateKey(date);
    const bookings=reservations.filter((item)=>overlapsDay(item,key));const statuses=new Set(bookings.map((item)=>item.estado));
    const classes=["day"];if(date.getMonth()!==visibleMonth.getMonth())classes.push("outside");if(key===selectedDate)classes.push("selected");if(key===today)classes.push("today");
    const button=make("button",classes.join(""));button.type="button";button.setAttribute("role","gridcell");button.setAttribute("aria-pressed",String(key===selectedDate));
    button.setAttribute("aria-label",formatLongDate(key)+", "+bookings.length+" reserva(s) activa(s)");
    const number=make("span","day-number",String(date.getDate()));const markers=make("span","day-markers");
    for(const status of statuses)markers.append(make("span","marker"+(status==="pendiente"?" pending":"")));
    const count=make("span","day-count",bookings.length?bookings.length+" "+(bookings.length===1?"estancia":"estancias"):"");
    button.append(number,markers,count);button.addEventListener("click",()=>{selectedDate=key;renderCalendar();renderAgenda()});calendarDays.append(button);
  }
  renderSummary();
}
function renderSummary(){
  if(!token){document.querySelector("#month-count").textContent="—";document.querySelector("#today-count").textContent="—";document.querySelector("#arrival-count").textContent="—";return}
  const list=monthReservations(visibleMonth);const today=dateKey(new Date());
  const rooms=new Set(reservations.filter((item)=>overlapsDay(item,today)).map((item)=>item.habitacion.trim().toLocaleLowerCase("es")));
  const first=dateKey(startOfMonth(visibleMonth));const next=dateKey(new Date(visibleMonth.getFullYear(),visibleMonth.getMonth()+1,1));
  const arrivals=reservations.filter((item)=>active(item)&&item.fecha_entrada>=first&&item.fecha_entrada<next).length;
  document.querySelector("#month-count").textContent=String(list.length);document.querySelector("#today-count").textContent=String(rooms.size);document.querySelector("#arrival-count").textContent=String(arrivals);
}
function dayEvent(item){if(item.estado==="cancelada")return "Reserva cancelada";if(item.fecha_entrada===selectedDate)return "Entrada";if(item.fecha_salida===selectedDate)return "Salida";return "En estancia"}
function renderAgenda(){
  const label=formatLongDate(selectedDate);document.querySelector("#selected-label").textContent=label.charAt(0).toLocaleUpperCase("es-CO")+label.slice(1);agenda.replaceChildren();
  const list=reservations.filter((item)=>item.fecha_entrada<=selectedDate&&item.fecha_salida>=selectedDate).sort((a,b)=>a.fecha_entrada.localeCompare(b.fecha_entrada));
  if(!list.length){agenda.append(make("p","empty","No hay reservas para este día. Puedes crear una estancia desde aquí."));return}
  for(const item of list){
    const entry=make("article","booking fade-in");const top=make("div","booking-top");const guest=make("div");
    guest.append(make("p","booking-guest",item.huesped||"Huésped"));guest.append(make("p","booking-room","Habitación "+item.habitacion+" · "+item.numero_huespedes+" huésped(es)"));
    const statusClass=item.estado==="cancelada"?"cancelled":item.estado==="pendiente"?"pending":"";
    const statusLabel=item.estado==="cancelada"?"Cancelada":item.estado==="pendiente"?"Pendiente":"Confirmada";
    top.append(guest,make("span","status "+statusClass,statusLabel));entry.append(top);
    entry.append(make("p","booking-dates",dayEvent(item)+" · "+formatShortDate(item.fecha_entrada)+" — "+formatShortDate(item.fecha_salida)));
    if(item.correo)entry.append(make("span","booking-email",item.correo));agenda.append(entry);
  }
}
function updateAuthControls(){document.querySelector("#auth-button").textContent=token?"Cerrar sesión":"Iniciar sesión";const button=document.querySelector("#save-booking-button");button.disabled=!token;button.textContent=token?"Guardar reserva":"Inicia sesión para guardar"}
function openBookingDialog(){
  if(!token){document.querySelector("#auth-message").textContent="Inicia sesión antes de registrar una reserva.";document.querySelector("#auth-message").dataset.kind="";loginDialog.showModal();return}
  reservationForm.reset();reservationForm.elements.fecha_entrada.value=selectedDate;reservationForm.elements.fecha_salida.value=addDays(selectedDate,1);updateDateConstraints();bookingDialog.showModal()
}
function updateDateConstraints(){const entry=reservationForm.elements.fecha_entrada;const exit=reservationForm.elements.fecha_salida;exit.min=entry.value?addDays(entry.value,1):"";if(entry.value&&exit.value&&exit.value<=entry.value)exit.value=addDays(entry.value,1)}
async function apiRequest(url,options){const response=await fetch(API_BASE_URL+url,options);const data=await response.json().catch(()=>({}));if(!response.ok)throw new Error(data.error||"La API respondió HTTP "+response.status+".");return data}
async function loadReservations(){
  if(!token){return}
  updateApiState("loading","Conectando");
  try{const data=await apiRequest("/reservas",{headers:{Accept:"application/json","Authorization":"Bearer "+token}});if(!Array.isArray(data))throw new Error("La respuesta de /reservas no tiene el formato esperado.");reservations.splice(0,reservations.length,...data);updateApiState("online","API conectada");setMessage(data.length+" reserva(s) cargada(s).","success");renderCalendar();renderAgenda()}
  catch(error){updateApiState("error","API sin conexión");setMessage(error.message,"error");renderCalendar();renderAgenda()}
}
document.querySelector("#previous-month").addEventListener("click",()=>{visibleMonth=new Date(visibleMonth.getFullYear(),visibleMonth.getMonth()-1,1);selectedDate=dateKey(visibleMonth);renderCalendar();renderAgenda()});
document.querySelector("#next-month").addEventListener("click",()=>{visibleMonth=new Date(visibleMonth.getFullYear(),visibleMonth.getMonth()+1,1);selectedDate=dateKey(visibleMonth);renderCalendar();renderAgenda()});
document.querySelector("#today-button").addEventListener("click",()=>{const today=new Date();visibleMonth=startOfMonth(today);selectedDate=dateKey(today);renderCalendar();renderAgenda()});
document.querySelector("#new-booking-button").addEventListener("click",openBookingDialog);
document.querySelector("#side-new-button").addEventListener("click",openBookingDialog);
document.querySelector("#auth-button").addEventListener("click",()=>{if(token){token=null;reservations.splice(0,reservations.length);updateAuthControls();renderCalendar();renderAgenda();updateApiState("loading","Inicia sesión");setMessage("Inicia sesión para consultar las reservas.");return}document.querySelector("#auth-message").textContent="";loginDialog.showModal()});
document.querySelector("#login-form").addEventListener("submit",async(event)=>{
  event.preventDefault();const form=new FormData(event.currentTarget);const status=document.querySelector("#auth-message");status.textContent="Validando credenciales…";status.dataset.kind="";
  try{const data=await apiRequest("/login",{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify({username:form.get("username"),clave:form.get("clave")})});token=data.token;updateAuthControls();status.textContent="Sesión iniciada como "+data.username+".";status.dataset.kind="success";event.currentTarget.reset();await loadReservations();window.setTimeout(()=>loginDialog.close(),550)}
  catch(error){token=null;updateAuthControls();status.textContent=error.message;status.dataset.kind="error"}
});
reservationForm.elements.fecha_entrada.addEventListener("change",updateDateConstraints);reservationForm.elements.fecha_salida.addEventListener("change",updateDateConstraints);
reservationForm.addEventListener("submit",async(event)=>{
  event.preventDefault();if(!token)return;const button=document.querySelector("#save-booking-button");const form=new FormData(reservationForm);const booking=Object.fromEntries(form.entries());booking.numero_huespedes=Number(booking.numero_huespedes);button.disabled=true;button.textContent="Guardando…";
  try{const data=await apiRequest("/reservas",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+token,Accept:"application/json"},body:JSON.stringify(booking)});bookingDialog.close();setMessage(data.message||"Reserva creada.","success");await loadReservations();renderAgenda()}
  catch(error){setMessage(error.message,"error")}finally{updateAuthControls()}
});
document.querySelectorAll("[data-close]").forEach((button)=>button.addEventListener("click",()=>document.getElementById(button.dataset.close).close()));
[bookingDialog,loginDialog].forEach((dialog)=>dialog.addEventListener("click",(event)=>{const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close()}));
updateAuthControls();renderCalendar();renderAgenda();updateApiState("loading","Inicia sesión");setMessage("Inicia sesión para consultar las reservas.");
