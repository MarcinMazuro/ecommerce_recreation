<div id="_desktop_contact_link">
  <div id="contact-link" style="display: flex; align-items: center; flex-wrap: wrap; justify-content: center; width: 100%; padding: 0;">
    
    <a href="https://localhost:8443/content/4-o-nas" style="margin-right: 5px; font-weight: bold; color: #87ab3e; text-decoration: none; font-size: 11px;">
      O nas
    </a>
    <span style="margin-right: 5px; margin-left: 5px; color: #ccc; font-size: 11px;">|</span>

    <a href="https://localhost:8443/content/6-faq" style="margin-right: 5px; font-weight: bold; color: #87ab3e; text-decoration: none; font-size: 11px;">
      FAQ
    </a>
    <span style="margin-right: 5px; margin-left: 5px; color: #ccc; font-size: 11px;">|</span>

    <a href="https://localhost:8443/content/1-wysylka" style="margin-right: 5px; font-weight: bold; color: #87ab3e; text-decoration: none; font-size: 11px;">
      Wysyłka
    </a>
    <span style="margin-right: 5px; margin-left: 5px; color: #ccc; font-size: 11px;">|</span>

    <a href="https://localhost:8443/contact-us" style="margin-right: 5px; font-weight: bold; color: #87ab3e; text-decoration: none; font-size: 11px;">
      Kontakt z Dobre Ziele
    </a>

    <span style="margin-right: 5px; margin-left: 5px; color: #ccc; font-size: 11px;">|</span>
    <a href="https://localhost:8443/923-promocje" style="margin-right: 5px; font-weight: bold; color: #87ab3e; text-decoration: none; font-size: 11px;">
      Promocje
    </a>

    {* Opcjonalnie: Jeśli w panelu podasz numer telefonu, wyświetli się on na końcu *}
    {if $contact_infos.phone}
       <span style="margin: 0 5px; color: #ccc; font-size: 11px;">|</span>
       <span style="color: #666; font-size: 11px;">
         Tel: {$contact_infos.phone}
       </span>
    {/if}

  </div>
</div>