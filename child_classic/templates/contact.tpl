{extends file='layouts/layout-full-width.tpl'}

{block name='content'}
<style>
    .contact-rich-page {
        font-family: 'Open Sans', Helvetica, Arial, sans-serif;
        color: #414141;
        padding-top: 20px;
        padding-bottom: 40px;
    }
    .contact-rich-page h1 {
        color: #333;
        font-weight: 700;
        margin-bottom: 40px;
        text-align: center;
        text-transform: uppercase;
        font-size: 1.8rem;
    }
    
    /* Lewa kolumna - Informacje */
    .info-column {
        padding-right: 30px;
    }
    .contact-info-box h2 {
        color: #5cb85c;
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 0;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    .contact-info-box p {
        font-size: 15px;
        margin-bottom: 15px;
        line-height: 1.6;
    }
    .contact-info-box a {
        color: #333;
        text-decoration: none;
        transition: color 0.2s;
    }
    .contact-info-box a:hover {
        color: #5cb85c;
    }
    
    /* Link "Więcej o sklepie" */
    .about-link {
        font-size: 1.1rem;
        font-weight: bold;
        margin-top: 25px;
        display: block;
    }
    .about-link a {
        color: #5cb85c;
        text-decoration: underline;
    }
    
    /* Alert - Sklep zamknięty */
    .alert-box-custom {
        background: #fff;
        border: 1px solid #eee;
        border-left: 5px solid #d9534f;
        padding: 20px;
        margin-top: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Prawa kolumna - Formularz */
    .contact-form-container {
        background: #ffffff;
        padding: 40px;
        border-radius: 4px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    
    /* Fixy do formularza PrestaShop */
    .contact-form-container .form-control {
        background: #f9f9f9;
        border: 1px solid #e5e5e5;
        padding: 12px;
        height: auto;
    }
    
    /* Przycisk WYŚLIJ */
    .contact-form-container .btn-primary, 
    .contact-form-container input.btn[type="submit"],
    .contact-form-container button[type="submit"] {
        background-color: #5cb85c !important;
        border-color: #5cb85c !important;
        color: #fff !important;
        font-weight: bold;
        text-transform: uppercase;
        padding: 12px 40px;
        border-radius: 3px;
        font-size: 1rem;
        transition: all 0.3s ease;
        margin-top: 15px;
        width: 100%;
    }
    .contact-form-container .btn-primary:hover {
        background-color: #449d44 !important;
    }

    /* Mapa */
    .map-section {
        margin-top: 0;
        margin-bottom: -20px;
        width: 100%;
        line-height: 0; /* Usuwa biały pasek pod mapą */
    }
    
    @media (max-width: 768px) {
        .info-column { padding-right: 15px; margin-bottom: 40px; }
    }
</style>

<div class="container contact-rich-page">
    
    <h1>Kontakt z Dobre Ziele</h1>
    
    <div class="row">
        
        <div class="col-lg-5 col-md-12 info-column">
            <div class="contact-info-box">
                <h2>Sklep internetowy<br>DobreZiele.pl</h2>
                
                <p>
                    ul. Kolbego 14a, 32-600 Oświęcim<br>
                    <strong>Telefon: <a href="tel:+48531050300" style="font-weight:bold; font-size:1.1em;">531 050 300</a></strong>
                </p>
                
                <hr style="border-top: 1px solid #f0f0f0; margin: 25px 0;">

                <p><strong>Magazyn wysyłkowy czynny:</strong><br>
                Pn-Pt: 7:00 - 15:00<br>
                Soboty: nieczynne</p>
                
                <p style="margin-top: 20px;">
                    <strong>NAPISZ DO NAS:</strong><br>
                    <a href="mailto:yerba@dobreziele.pl" style="color: #5cb85c; font-weight: bold; font-size: 1.3em;">yerba@dobreziele.pl</a>
                </p>

                <div class="about-link">
                    <h3>Więcej o sklepie Dobre Ziele <a href="https://localhost:8443/content/4-o-nas" target="_blank">przeczytasz TUTAJ</a>.</h3>
                </div>

                <div class="alert-box-custom">
                    <h4 style="font-size: 16px; font-weight: bold; margin-top:0; color: #d9534f;">Sklep w Krakowie - nieczynny</h4>
                    <p style="font-size: 14px; margin-bottom: 0;">Uwaga! Nasz sklep stacjonarny w Krakowie został zamknięty. Zapraszamy na zakupy online.</p>
                </div>
            </div>
        </div>

        <div class="col-lg-7 col-md-12">
            <div class="contact-form-container">
                <h3 style="margin-top: 0; margin-bottom: 25px; font-size: 1.2rem; text-transform: uppercase; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; font-weight: bold;">Formularz kontaktowy</h3>
                
                {widget name="contactform"}
                
            </div>
        </div>

    </div>
</div>

<div class="map-section">
    <iframe 
        width="100%" 
        height="450" 
        frameborder="0" 
        scrolling="no" 
        marginheight="0" 
        marginwidth="0" 
        src="https://maps.google.com/maps?q=ul.+Maksymiliana+Kolbego+14a,+32-600+O%C5%9Bwi%C4%99cim&t=&z=15&ie=UTF8&iwloc=&output=embed">
    </iframe>
</div>

{/block}