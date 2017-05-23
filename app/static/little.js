function change_price(){
    var checkboxList = document.getElementsByClassName('judge-choose');
    var priceList = document.getElementsByClassName('price-cart-p');
    var totalPrice = 0;
    for(let i = 0;i<checkboxList.length;i++){
      if(checkboxList[i].checked){
          totalPrice +=Number(priceList[i].innerText);
          console.log(totalPrice);
      }
    }
    var totalPriceLabel = document.getElementById('total_price');
    totalPriceLabel.innerText = totalPrice.toString() + ' 元';
}