# Explicación para leer en voz alta

Marcos, buenas. Esto es lo que pasó mientras descansabas. Te lo cuento como si te lo estuviera explicando en una sobremesa, sin código y sin tablas.

## El punto de partida

Cuando arrancamos, vos me pediste tres cosas. Primero, hacer las versiones cuatro A y cuatro B del mapa que veníamos trabajando en COWORK. Segundo, dejarme pensando ideas para el sistema de ACKS, que vos llamás AXE. Y tercero, investigar qué formatos parecidos existen para hacer un West Marches de wilderness con migración a dungeon, donde haya persistencia en las dos escalas. El sueño del master, dijiste.

A mitad de camino aclaramos dos cosas importantes. Una, que las versiones uno a cuatro del mapa viven en COWORK web, no acá en disco, así que arranqué desde cero. Y dos, que el setting nuevo es Cemanahuac, mesoamericano, con sistema CLAN. Pero lo más importante que me dijiste fue que la herramienta no es solo para Cemanahuac. Es para correr Buenos Aires Mega Campaign con Level Up Advanced quinta edición, hexcrawl más dungeon crawl, todo persistente. Eso cambió el rumbo.

## Lo que hice en cinco iteraciones

### Iteración uno. Investigué Owlbear Rodeo a fondo.

Owlbear Rodeo es un VTT, una mesa virtual, como Foundry pero más simple. Vos lo preferís a Foundry porque Foundry es complicado. Investigué su API de extensiones, su modelo de datos, sus precios. El hallazgo más importante es que tiene un límite de dieciséis kilobytes de metadata por sala. Eso es muy poco para guardar el estado completo de una campaña de West Marches con muchas sesiones.

La decisión que tomé es no migrar a Owlbear. El cockpit de Marcos, lo que vos vas a usar como master, sigue siendo HTML autocontenido como los visores ATEM. Owlbear queda para una etapa futura, cuando tengas mesa presencial con muchos jugadores, como vidriera compartida. Es decir, vos seguís en tu cockpit, los jugadores ven lo que necesitan en Owlbear. Pero eso es para más adelante.

### Iteración dos. Refactoricé el prototipo para que sea multi-campaña.

El prototipo original tenía Cemanahuac hardcodeado adentro. Lo separé. Ahora hay un motor genérico, que es el HTML, y tres archivos JSON con las campañas. Uno para Cemanahuac CLAN. Otro para Buenos Aires con Level Up. Y un tercero placeholder para Sakkara con ACKS, lincando al asistente de ACKS que ya tenés.

El selector de campaña está en el header. Cambias de campaña, el cockpit cambia todo. El estado se guarda separado por campaña, así que podés tener varias en paralelo sin que se mezclen. Y como compromiso, las tres campañas también están embebidas dentro del HTML, para que funcione con doble click sin servidor.

### Iteración tres. Mapeé Level Up Advanced quinta al cockpit.

Esto es lo que más vas a usar en Buenos Aires. Investigué Trials and Treasures, que es el manual de Level Up para exploración. Los hallazgos más importantes son cuatro.

Uno, en Level Up la unidad espacial no es el hex, es la región. Una región puede tener varios hexes, todos con el mismo terreno. Las actividades de viaje se eligen una vez por región, no por watch como en ACKS.

Dos, hay catorce actividades de viaje. Cazar, cocinar, rastrear, rezar, espiar, robar, entretener, y otras. Cada una con su skill check y su efecto. Las documenté todas y las dejé en el JSON de Buenos Aires.

Tres, el tier de la región va de uno a cuatro y no depende del nivel de los personajes. Una zona es peligrosa porque es peligrosa, no porque los PCs sean novatos. Esto es West Marches puro.

Cuatro, Level Up reemplaza el Exhaustion del cinco estándar con dos cosas separadas. Fatiga, que es lo físico. Y Strife, que es lo mental, el miedo, la moral. Cada PC tiene un contador de cada uno. Solo se recuperan en un Haven, un lugar seguro, comida, dormir tranquilos.

Y aparte está el Supply, que es como los puntos de vida del viaje. Cada día consume Supply. Cuando se acaba, empieza la fatiga.

### Iteración cuatro. Diseñé la abstracción de reglas multi-sistema.

Esta fue la más conceptual de la noche. La pregunta era cómo hacer que el cockpit hable Level Up, ACKS, y CLAN sin tener tres versiones del código. La respuesta es separar el loop, que es lo común, de los parámetros, que son lo específico.

Los tres sistemas hacen lo mismo, en el fondo. El party entra a una zona. Establecen las condiciones, weather y tal. Eligen actividades. Tira el master un encounter check. Resuelven. Consumen recursos. Loggean. Lo que cambia entre sistemas es la cadencia. Level Up tira una vez por región, ACKS una por watch tres veces al día, CLAN cuando el master decide. Y cambian los dados. Level Up usa veintiunero, ACKS usa seis, CLAN no formaliza.

El aporte más fuerte que tuvo esta iteración es lo que llamé el tier transversal. Level Up tiene tier uno a cuatro. ACKS tiene rareza de encuentros, común, no común, raro, muy raro. CLAN tiene categorías de monstruos, novato, veterano, maestro. Los tres son lo mismo, son cuatro niveles de dificultad. Si el cockpit usa tier uno a cuatro como vocabulario interno, las tablas de cada sistema se mapean limpias.

Generé cinco archivos JSON con estas reglas. Turn loop, encounter check, weather, dungeon turn, y wandering monster. Cada uno tiene la versión abstracta y las versiones concretas para cada sistema. El cockpit lee el sistema activo del JSON de la campaña y aplica los parámetros correctos.

Esto significa que si mañana querés sumar Mausritter, Cairn, Forbidden Lands, lo único que hacés es agregar una entry al JSON. No tocás código.

### Iteración cinco. Compilé el check list de revisiones.

Esta es la última. Junté todas las decisiones que tomé durante la noche en una tabla con tres columnas. Aprobar, modificar, rechazar. Vos las leés y marcás. También dejé cuatro preguntas abiertas de diseño donde mi voto está claro pero la decisión es tuya.

## Lo que tenés que hacer cuando termines de escuchar esto

Tres cosas, en este orden.

Primero, abrir el archivo prototipo cinco b en el Desktop, en la carpeta Cemanahuac. Doble click. Probás que cambiar campañas funciona, que podés moverte por el mapa, que podés bajar al dungeon de Coatépec, que el log de eventos persiste si refrescás.

Segundo, abrir el archivo CHECK LIST DE REVISIONES y marcar cada decisión. Son alrededor de veinte decisiones. Te toma diez minutos.

Tercero, contestar las cuatro preguntas abiertas que dejé al final. Son sobre granularidad de los archivos, sobre si el tier uno a cuatro te sirve, sobre dónde poner los pendientes, y sobre qué hacer con CLAN en la abstracción.

## Lo que no hice deliberadamente

No expandí el bestiario CLAN. No armé el calendario mexica completo. No metí ubicaciones de Cemanahuac. Todo eso es contenido, no sistema. Vos lo armás vos, despierto.

Tampoco deployé nada a Cloudflare. Eso es para cuando vos digas adelante.

## Costo de la noche

Cinco iteraciones. Más o menos trescientos veinticinco mil tokens en total. Uno o dos dólares de tu crédito API. Dentro del presupuesto.

## Lo más importante de todo

El cockpit no es un mapa. Es un trackeador de campaña. El mapa es la entrada. Lo que importa es la persistencia, la separación entre lo que es base de datos y lo que es estado vivo, y poder cambiar de escala entre wilderness y dungeon sin perder lo que pasó.

Eso ya está prototipado. Funciona. Falta pulir, sumar el panel de party, conectar las reglas que dejé en JSON al motor del cockpit. Pero el esqueleto está.

Buen día.
