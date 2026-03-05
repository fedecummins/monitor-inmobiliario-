const datos = [
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 250000,
    ambientes: 3,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-vicente-lopez.html",
    historialPrecios: [260000, 250000],
    imagen: "https://via.placeholder.com/350x180?text=Casa+Vicente+Lopez"
  },
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 330000,
    ambientes: 4,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-vicente-lopez.html",
    historialPrecios: [335000, 330000],
    imagen: "https://via.placeholder.com/350x180?text=PH+Vicente+Lopez"
  },
  {
    barrio: "Vicente López",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 370000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-vicente-lopez",
    historialPrecios: [365000, 370000],
    imagen: "https://via.placeholder.com/350x180?text=Terreno+Vicente+Lopez"
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 230000,
    ambientes: 2,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-florida.html",
    historialPrecios: [230000, 230000],
    imagen: "https://via.placeholder.com/350x180?text=Casa+Florida"
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 350000,
    ambientes: 3,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-florida.html",
    historialPrecios: [355000, 350000],
    imagen: "https://via.placeholder.com/350x180?text=PH+Florida"
  },
  {
    barrio: "Florida",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 300000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-florida",
    historialPrecios: [310000, 300000],
    imagen: "https://via.placeholder.com/350x180?text=Terreno+Florida"
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "casa",
    precio: 300000,
    ambientes: 4,
    sitio: "Zonaprop",
    link: "https://www.zonaprop.com.ar/casa-en-venta-la-lucila.html",
    historialPrecios: [295000, 300000],
    imagen: "https://via.placeholder.com/350x180?text=Casa+La+Lucila"
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "ph",
    precio: 220000,
    ambientes: 2,
    sitio: "Argenprop",
    link: "https://www.argenprop.com/ph-en-venta-la-lucila.html",
    historialPrecios: [220000, 220000],
    imagen: "https://via.placeholder.com/350x180?text=PH+La+Lucila"
  },
  {
    barrio: "La Lucila",
    tipoOperacion: "venta",
    tipoPropiedad: "terreno",
    precio: 380000,
    ambientes: null,
    sitio: "MercadoLibre",
    link: "https://inmuebles.mercadolibre.com.ar/terreno-en-venta-la-lucila",
    historialPrecios: [385000, 380000],
    imagen: "https://via.placeholder.com/350x180?text=Terreno+La+Lucila"
  }
];

function variacionPrecio(historial) {
  const antes = historial[0], ahora = historial[historial.length - 1];
  if (antes < ahora) return "Subió";
  if (antes > ahora) return "Bajó";
  return "Sin cambios";
}

function mostrarDatos() {
  const barrioSeleccionado = document.getElementById('barrio').value;
  const tipoOperacionSeleccionado = document.getElementById('tipoOperacion').value;
  const tipoPropiedadSeleccionado = document.getElementById('tipoPropiedad').value;
  const precioMin = parseInt(document.getElementById('precioMin').value, 10);
  const precioMax = parseInt(document.getElementById('precioMax').value, 10);

  const filtrados = datos.filter(d =>
    d.barrio === barrioSeleccionado &&
    d.tipoOperacion === tipoOperacionSeleccionado &&
    d.tipoPropiedad === tipoPropiedadSeleccionado &&
    d.precio >= precioMin &&
    d.precio <= precioMax
  );

  const contenidoDiv = document.getElementById('contenido');

  if (filtrados.length === 0) {
    contenidoDiv.innerHTML = `<div class="alert alert-warning">No hay propiedades para los criterios seleccionados.</div>`;
    return;
  }

  contenidoDiv.innerHTML = `
    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
      ${filtrados.map(d => `
        <div class="col">
          <div class="card h-100 shadow-sm">
            <a href="${d.link}" target="_blank" rel="noopener">
              <img src="${d.imagen}" class="card-img-top" alt="Foto de la propiedad">
            </a>
            <div class="card-body">
              <h5 class="card-title">${d.tipoPropiedad[0].toUpperCase() + d.tipoPropiedad.slice(1)} en ${d.barrio}</h5>
              <p class="card-text mb-1"><b>Sitio:</b> <a href="${d.link}" target="_blank">${d.sitio}</a></p>
              <p class="card-text mb-1"><b>Ambientes:</b> ${d.ambientes ?? '-'}</p>
              <p class="card-text mb-1"><b>Precio:</b> USD ${d.precio.toLocaleString()}</p>
              <span class="badge bg-${
                (function(v){
                  if(v==="Subió")return"success";
                  if(v==="Bajó")return"danger";
                  return"secondary";
                })(variacionPrecio(d.historialPrecios))
              }">${variacionPrecio(d.historialPrecios)}</span>
            </div>
            <div class="card-footer">
              <a href="${d.link}" target="_blank" class="btn btn-primary w-100">Ver anuncio</a>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

document.querySelectorAll('#filtros select, #filtros input').forEach(el => {
  el.addEventListener('change', mostrarDatos);
  el.addEventListener('input', mostrarDatos);
});

mostrarDatos();