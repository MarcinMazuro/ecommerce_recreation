<div id="_desktop_contact_link">
  <div id="contact-link" style="display: flex; align-items: center;">
    
    <a href="https://localhost:8443/content/4-o-nas" style="margin-right: 10px; font-weight: bold; color: #87ab3e; text-decoration: none;">
      O nas
    </a>
    <span style="margin-right: 10px; color: #ccc;">|</span>

    <a href="https://localhost:8443/content/6-faq" style="margin-right: 10px; font-weight: bold; color: #87ab3e; text-decoration: none;">
      FAQ
    </a>
    <span style="margin-right: 10px; color: #ccc;">|</span>

    <a href="https://localhost:8443/content/1-wysylka" style="margin-right: 10px; font-weight: bold; color: #87ab3e; text-decoration: none;">
      Wysyłka
    </a>
    <span style="margin-right: 10px; color: #ccc;">|</span>

    <a href="https://localhost:8443/contact-us" style="font-weight: bold; color: #87ab3e; text-decoration: none;">
      Kontakt z Dobre Ziele
    </a>

    {* Opcjonalnie: Jeśli w panelu podasz numer telefonu, wyświetli się on na końcu *}
    {if $contact_infos.phone}
       <span style="margin: 0 10px; color: #ccc;">|</span>
       <span style="color: #666;">
         Tel: {$contact_infos.phone}
       </span>
    {/if}

  </div>
</div>