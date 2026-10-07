

const canteenFoodList = [
  {
    name: "Samosa",
    category: "snack",
    vegetarian: true,
    price: 15,
    image: "https://www.google.com/search?tbm=isch&q=samosa"
  },
  {
    name: "Kachori",
    category: "snack",
    vegetarian: true,
    price: 15,
    image: "https://www.google.com/search?tbm=isch&q=kachori"
  },
  {
    name: "Pakora",
    category: "snack",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=pakora"
  },
  {
    name: "Vada Pav",
    category: "snack",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=vada+pav"
  },
  {
    name: "Bread Pakora",
    category: "snack",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=bread+pakora"
  },
  {
    name: "Aloo Tikki",
    category: "snack",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=aloo+tikki"
  },
  {
    name: "Poha",
    category: "breakfast",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=poha"
  },
  {
    name: "Upma",
    category: "breakfast",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=upma"
  },
  {
    name: "Idli",
    category: "breakfast",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=idli"
  },
  {
    name: "Dosa",
    category: "breakfast",
    vegetarian: true,
    price: 40,
    image: "https://www.google.com/search?tbm=isch&q=dosa"
  },
  {
    name: "Masala Dosa",
    category: "breakfast",
    vegetarian: true,
    price: 50,
    image: "https://www.google.com/search?tbm=isch&q=masala+dosa"
  },
  {
    name: "Aloo Paratha",
    category: "breakfast",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=aloo+paratha"
  },
  {
    name: "Chole Bhature",
    category: "main",
    vegetarian: true,
    price: 60,
    image: "https://www.google.com/search?tbm=isch&q=chole+bhature"
  },
  {
    name: "Rajma Chawal",
    category: "main",
    vegetarian: true,
    price: 60,
    image: "https://www.google.com/search?tbm=isch&q=rajma+chawal"
  },
  {
    name: "Dal Chawal",
    category: "main",
    vegetarian: true,
    price: 50,
    image: "https://www.google.com/search?tbm=isch&q=dal+chawal"
  },
  {
    name: "Dal Roti",
    category: "main",
    vegetarian: true,
    price: 50,
    image: "https://www.google.com/search?tbm=isch&q=dal+roti"
  },
  {
    name: "Kadhai Paneer",
    category: "main",
    vegetarian: true,
    price: 80,
    image: "https://www.google.com/search?tbm=isch&q=kadhai+paneer"
  },
  {
    name: "Shahi Paneer",
    category: "main",
    vegetarian: true,
    price: 80,
    image: "https://www.google.com/search?tbm=isch&q=shahi+paneer"
  },
  {
    name: "Aloo Gobi",
    category: "main",
    vegetarian: true,
    price: 60,
    image: "https://www.google.com/search?tbm=isch&q=aloo+gobi"
  },
  {
    name: "Mix Veg",
    category: "main",
    vegetarian: true,
    price: 60,
    image: "https://www.google.com/search?tbm=isch&q=mix+veg+indian"
  },
  {
    name: "Chole",
    category: "main",
    vegetarian: true,
    price: 50,
    image: "https://www.google.com/search?tbm=isch&q=chole+indian"
  },
  {
    name: "Veg Biryani",
    category: "main",
    vegetarian: true,
    price: 70,
    image: "https://www.google.com/search?tbm=isch&q=veg+biryani"
  },
  {
    name: "Egg Biryani",
    category: "main",
    vegetarian: false,
    price: 90,
    image: "https://www.google.com/search?tbm=isch&q=egg+biryani"
  },
  {
    name: "Chicken Biryani",
    category: "main",
    vegetarian: false,
    price: 100,
    image: "https://www.google.com/search?tbm=isch&q=chicken+biryani"
  },
  {
    name: "Egg Curry",
    category: "main",
    vegetarian: false,
    price: 60,
    image: "https://www.google.com/search?tbm=isch&q=egg+curry"
  },
  {
    name: "Chicken Curry",
    category: "main",
    vegetarian: false,
    price: 100,
    image: "https://www.google.com/search?tbm=isch&q=chicken+curry"
  },
  {
    name: "Rice",
    category: "staple",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=indian+rice"
  },
  {
    name: "Roti",
    category: "staple",
    vegetarian: true,
    price: 10,
    image: "https://www.google.com/search?tbm=isch&q=roti"
  },
  {
    name: "Naan",
    category: "staple",
    vegetarian: true,
    price: 25,
    image: "https://www.google.com/search?tbm=isch&q=naan"
  },
  {
    name: "Curd",
    category: "side",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=indian+curd+dahi"
  },
  {
    name: "Raita",
    category: "side",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=raita"
  },
  {
    name: "Papad",
    category: "side",
    vegetarian: true,
    price: 10,
    image: "https://www.google.com/search?tbm=isch&q=papad"
  },
  {
    name: "Pickle",
    category: "side",
    vegetarian: true,
    price: 10,
    image: "https://www.google.com/search?tbm=isch&q=indian+pickle+achar"
  },
  {
    name: "Gulab Jamun",
    category: "dessert",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=gulab+jamun"
  },
  {
    name: "Jalebi",
    category: "dessert",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=jalebi"
  },
  {
    name: "Rasgulla",
    category: "dessert",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=rasgulla"
  },
  {
    name: "Kheer",
    category: "dessert",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=kheer"
  },
  {
    name: "Tea",
    category: "beverage",
    vegetarian: true,
    price: 10,
    image: "https://www.google.com/search?tbm=isch&q=indian+chai"
  },
  {
    name: "Coffee",
    category: "beverage",
    vegetarian: true,
    price: 20,
    image: "https://www.google.com/search?tbm=isch&q=indian+coffee"
  },
  {
    name: "Lassi",
    category: "beverage",
    vegetarian: true,
    price: 30,
    image: "https://www.google.com/search?tbm=isch&q=lassi"
  },
  {
    name: "Lemon Water",
    category: "beverage",
    vegetarian: true,
    price: 15,
    image: "https://www.google.com/search?tbm=isch&q=lemon+water"
  }
];

export default canteenFoodList;